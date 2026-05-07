"""REST API для задач binding-site detection."""

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from ..models.pocket import JobResult
from ..services import binding_site as svc

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", status_code=201)
async def create_job(
    background: BackgroundTasks,
    pdb_id: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
) -> dict:
    """Создать задачу. Либо pdb_id (form-data), либо file (multipart)."""

    if not pdb_id and not file:
        raise HTTPException(400, "either pdb_id or file is required")

    job_id = svc.create_job(pdb_id=pdb_id)

    if file is not None:
        target = svc.get_input_pdb_path(job_id)
        target.write_bytes(await file.read())

    background.add_task(svc.run_job, job_id)
    return {"job_id": job_id}


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
