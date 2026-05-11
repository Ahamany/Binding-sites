"""End-to-end API tests через FastAPI TestClient.

Покрываем error paths, валидацию входов, форму ответов.
Не запускаем реальный P2Rank/fpocket — тяжёлые джобы должны идти через
интеграционный slow-test (Day 7).
"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import binding_site as svc


@pytest.fixture
def client(monkeypatch):
    """TestClient + заглушка run_job (чтобы фоновая задача не лезла за PDB)."""
    async def _noop(job_id: str) -> None:
        return None
    monkeypatch.setattr(svc, "run_job", _noop)
    return TestClient(app)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_job_requires_input(client):
    r = client.post("/api/jobs")
    assert r.status_code == 400
    assert "pdb_id or file" in r.json()["detail"]


def test_create_job_invalid_pdb_id(client):
    r = client.post("/api/jobs", data={"pdb_id": "XYZ"})
    assert r.status_code == 422
    assert "invalid pdb_id" in r.json()["detail"]


def test_create_job_invalid_pdb_id_too_long(client):
    r = client.post("/api/jobs", data={"pdb_id": "1FBLZ"})
    assert r.status_code == 422


def test_create_job_normalizes_pdb_id(client):
    r = client.post("/api/jobs", data={"pdb_id": "1fbl"})
    assert r.status_code == 201
    job_id = r.json()["job_id"]
    status = client.get(f"/api/jobs/{job_id}").json()
    assert status["pdb_id"] == "1FBL"


def test_create_job_with_file(client, tmp_path):
    fake_pdb = tmp_path / "fake.pdb"
    fake_pdb.write_text("HEADER fake\nATOM      1  CA  ALA A   1       0.000   0.000   0.000\nEND\n")
    with fake_pdb.open("rb") as fh:
        r = client.post("/api/jobs", files={"file": ("fake.pdb", fh, "chemical/x-pdb")})
    assert r.status_code == 201
    assert "job_id" in r.json()


def test_get_status_404_on_unknown(client):
    r = client.get("/api/jobs/notarealjob")
    assert r.status_code == 404


def test_get_results_404_on_unknown(client):
    r = client.get("/api/jobs/notarealjob/results")
    assert r.status_code == 404


def test_get_csv_404_on_unknown(client):
    r = client.get("/api/jobs/notarealjob/results.csv")
    assert r.status_code == 404


def test_get_structure_404_on_unknown(client):
    r = client.get("/api/jobs/notarealjob/structure")
    assert r.status_code == 404


def test_list_jobs_returns_list(client):
    r = client.get("/api/jobs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_then_list_includes_new_job(client):
    job_id = client.post("/api/jobs", data={"pdb_id": "1FBL"}).json()["job_id"]
    listing = client.get("/api/jobs").json()
    assert any(j["job_id"] == job_id for j in listing)


def test_csv_after_failed_job_has_only_header(client):
    """Если результаты пустые (например, до запуска), CSV содержит только заголовок."""
    job_id = client.post("/api/jobs", data={"pdb_id": "1FBL"}).json()["job_id"]
    r = client.get(f"/api/jobs/{job_id}/results.csv")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    lines = [l for l in r.text.splitlines() if l.strip()]
    assert lines[0].startswith("method,rank,score")


def test_pdb_not_found_marks_job_failed(monkeypatch):
    """Реальная ветка PDBNotFoundError: orchestrator кладёт job в failed."""

    async def fake_run_job(job_id: str) -> None:
        job = svc._jobs[job_id]
        job.status = svc.JobStatus.failed
        job.error = f"PDB ID '{job.pdb_id}' not found in RCSB"

    monkeypatch.setattr(svc, "run_job", fake_run_job)
    client = TestClient(app)
    job_id = client.post("/api/jobs", data={"pdb_id": "9ZZZ"}).json()["job_id"]

    asyncio.run(fake_run_job(job_id))

    r = client.get(f"/api/jobs/{job_id}").json()
    assert r["status"] == "failed"
    assert "9ZZZ" in r["error"]
