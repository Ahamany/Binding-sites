"""Тесты offline-кеша PDB (Risk R4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services import binding_site as svc


@pytest.fixture
def cache_dir(tmp_path, monkeypatch):
    cache = tmp_path / "pdb_cache"
    cache.mkdir()
    monkeypatch.setattr(svc, "PDB_CACHE_DIR", cache)
    return cache


def test_fetch_cache_hit_no_network(cache_dir, tmp_path, monkeypatch):
    (cache_dir / "1ABC.pdb").write_text("HEADER cached fake\n")

    def fail_get(*args, **kwargs):
        raise AssertionError("network must not be called on cache hit")

    monkeypatch.setattr(svc.requests, "get", fail_get)

    dest = tmp_path / "input.pdb"
    svc.fetch_pdb("1ABC", dest)
    assert dest.read_text() == "HEADER cached fake\n"


def test_fetch_cache_hit_normalises_case(cache_dir, tmp_path, monkeypatch):
    (cache_dir / "1FBL.pdb").write_text("HEADER FBL cached\n")
    monkeypatch.setattr(svc.requests, "get", lambda *a, **k: pytest.fail("no network"))

    dest = tmp_path / "input.pdb"
    svc.fetch_pdb("1fbl", dest)
    assert dest.read_text() == "HEADER FBL cached\n"


class _FakeResponse:
    def __init__(self, status_code: int, content: bytes = b"") -> None:
        self.status_code = status_code
        self.content = content

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise svc.requests.HTTPError(f"status {self.status_code}")


def test_fetch_cache_miss_writes_to_cache(cache_dir, tmp_path, monkeypatch):
    body = b"HEADER downloaded\nEND\n"

    def fake_get(url, timeout=30):
        assert "1XYZ" in url
        return _FakeResponse(200, body)

    monkeypatch.setattr(svc.requests, "get", fake_get)

    dest = tmp_path / "input.pdb"
    svc.fetch_pdb("1XYZ", dest)
    assert dest.read_bytes() == body
    assert (cache_dir / "1XYZ.pdb").read_bytes() == body


def test_fetch_404_does_not_pollute_cache(cache_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(
        svc.requests, "get", lambda url, timeout=30: _FakeResponse(404)
    )

    dest = tmp_path / "input.pdb"
    with pytest.raises(svc.PDBNotFoundError, match="9ZZZ"):
        svc.fetch_pdb("9ZZZ", dest)

    assert not (cache_dir / "9ZZZ.pdb").exists()
    assert not dest.exists()


def test_fetch_cache_disabled_when_dir_missing(tmp_path, monkeypatch):
    """Если data/pdb_cache/ нет — fetch падает на RCSB и НЕ создаёт кеш-папку."""
    no_cache = tmp_path / "absent"
    monkeypatch.setattr(svc, "PDB_CACHE_DIR", no_cache)

    body = b"HEADER plain fetch\n"
    monkeypatch.setattr(
        svc.requests,
        "get",
        lambda url, timeout=30: _FakeResponse(200, body),
    )

    dest = tmp_path / "input.pdb"
    svc.fetch_pdb("1WWW", dest)
    assert dest.read_bytes() == body
    assert not no_cache.exists()  # папку не создаём «втихую»
