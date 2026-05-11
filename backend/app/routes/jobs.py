"""REST API для задач binding-site detection."""

import csv
import io
import re
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response

from ..models.pocket import JobResult
from ..services import binding_site as svc

router = APIRouter(prefix="/jobs", tags=["jobs"])

PDB_ID_RE = re.compile(r"^[0-9][A-Za-z0-9]{3}$")


@router.post("", status_code=201)
async def create_job(
    background: BackgroundTasks,
    pdb_id: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
) -> dict:
    """Создать задачу. Либо pdb_id (form-data), либо file (multipart)."""

    if not pdb_id and not file:
        raise HTTPException(400, "either pdb_id or file is required")

    if pdb_id is not None:
        pdb_id = pdb_id.strip().upper()
        if not PDB_ID_RE.match(pdb_id):
            raise HTTPException(
                422,
                f"invalid pdb_id '{pdb_id}': expected 4 chars, "
                f"first digit, then alphanumeric (e.g. 1FBL)",
            )

    job_id = svc.create_job(pdb_id=pdb_id)

    if file is not None:
        target = svc.get_input_pdb_path(job_id)
        target.write_bytes(await file.read())

    background.add_task(svc.run_job, job_id)
    return {"job_id": job_id}


@router.get("")
def list_jobs() -> list[dict]:
    """Краткий листинг всех задач (debug/admin)."""
    return [
        {
            "job_id": j.job_id,
            "status": j.status,
            "pdb_id": j.pdb_id,
            "error": j.error,
        }
        for j in svc.list_jobs()
    ]


@router.get("/{job_id}")
def get_status(job_id: str) -> JobResult:
    job = svc.get_job(job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    return job


@router.get("/{job_id}/structure")
def get_structure(job_id: str) -> FileResponse:
    """Отдать очищенный PDB для отрисовки в 3Dmol.js."""
    job = svc.get_job(job_id)
    if job is None:
        raise HTTPException(404, "job not found")

    clean = svc.get_clean_pdb_path(job_id)
    raw = svc.get_input_pdb_path(job_id)
    path = clean if clean.exists() else raw
    if not path.exists():
        raise HTTPException(404, "PDB file not yet available")
    return FileResponse(path, media_type="chemical/x-pdb", filename=f"{job_id}.pdb")


@router.get("/{job_id}/results")
def get_results(job_id: str) -> JSONResponse:
    job = svc.get_job(job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    return JSONResponse(job.model_dump(mode="json"))


@router.get("/{job_id}/results.csv")
def get_results_csv(job_id: str) -> Response:
    """Скачать карманы плоской таблицей CSV."""
    job = svc.get_job(job_id)
    if job is None:
        raise HTTPException(404, "job not found")

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "method", "rank", "score",
            "center_x", "center_y", "center_z",
            "radius", "n_residues", "residues",
        ]
    )
    for method, mr in job.results.items():
        if mr.error:
            continue
        for p in mr.pockets:
            writer.writerow(
                [
                    method.value, p.rank, f"{p.score:.4f}",
                    f"{p.center[0]:.3f}", f"{p.center[1]:.3f}", f"{p.center[2]:.3f}",
                    "" if p.radius is None else f"{p.radius:.2f}",
                    len(p.residues),
                    " ".join(p.residues),
                ]
            )
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{job_id}.csv"'},
    )
