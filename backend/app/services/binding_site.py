"""Оркестрация: preprocess → запуск детекторов → агрегация.

In-memory job storage. Для MVP не нужна БД: задач немного, после рестарта чистим work/.
"""

import asyncio
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional

import requests

from ..eval.compare import compare_methods
from ..eval.dcc import evaluate_metrics, extract_ligand_center
from ..models.pocket import JobResult, JobStatus, Method, MethodResult
from ..tools.fpocket import run_fpocket
from ..tools.p2rank import run_p2rank
from ..tools.preprocess import preprocess_pdb

PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORK_DIR = PROJECT_ROOT / "work"
WORK_DIR.mkdir(parents=True, exist_ok=True)

# Offline-кеш PDB для демо без интернета (Risk R4). fetch_pdb сначала
# смотрит сюда, и автозаписывает успешные fetch'и при первой загрузке.
PDB_CACHE_DIR = PROJECT_ROOT / "data" / "pdb_cache"

_jobs: dict[str, JobResult] = {}


class PDBNotFoundError(Exception):
    """RCSB вернул 404 для запрошенного PDB ID."""


def list_jobs() -> list[JobResult]:
    return list(_jobs.values())


def get_job(job_id: str) -> Optional[JobResult]:
    return _jobs.get(job_id)


def create_job(pdb_id: Optional[str] = None) -> str:
    job_id = uuid.uuid4().hex[:12]
    _jobs[job_id] = JobResult(job_id=job_id, status=JobStatus.queued, pdb_id=pdb_id)
    (WORK_DIR / job_id).mkdir(parents=True, exist_ok=True)
    return job_id


def fetch_pdb(pdb_id: str, dest: Path) -> Path:
    """Получить PDB-файл: сначала из локального кеша, потом из RCSB.

    Cache hit  → copy data/pdb_cache/{PDB}.pdb → dest, без сети.
    Cache miss → fetch с RCSB, write to dest, и (если кеш-папка существует)
                 положить копию в кеш для будущих оффлайн-запусков.
    404        → PDBNotFoundError, в кеш ничего не пишется.
    """
    pdb_upper = pdb_id.upper()
    cached = PDB_CACHE_DIR / f"{pdb_upper}.pdb"
    if cached.exists():
        shutil.copyfile(cached, dest)
        return dest

    url = f"https://files.rcsb.org/download/{pdb_upper}.pdb"
    r = requests.get(url, timeout=30)
    if r.status_code == 404:
        raise PDBNotFoundError(f"PDB ID '{pdb_upper}' not found in RCSB")
    r.raise_for_status()
    dest.write_bytes(r.content)

    if PDB_CACHE_DIR.exists():
        try:
            shutil.copyfile(dest, cached)
        except OSError:
            pass  # кеш-промах не должен ломать пайплайн

    return dest


def get_input_pdb_path(job_id: str) -> Path:
    return WORK_DIR / job_id / "input.pdb"


def get_clean_pdb_path(job_id: str) -> Path:
    return WORK_DIR / job_id / "clean.pdb"


async def run_job(job_id: str) -> None:
    """Фоновая обработка: preprocess + параллельный запуск P2Rank/fpocket."""
    job = _jobs[job_id]
    job.status = JobStatus.running

    job_dir = WORK_DIR / job_id
    raw = get_input_pdb_path(job_id)
    clean = get_clean_pdb_path(job_id)

    try:
        if not raw.exists() and job.pdb_id:
            fetch_pdb(job.pdb_id, raw)

        if not raw.exists():
            raise FileNotFoundError(f"input PDB missing for job {job_id}")

        preprocess_pdb(raw, clean)

        loop = asyncio.get_running_loop()

        async def _run(method_fn, name: str) -> MethodResult:
            t0 = time.time()
            result: MethodResult = await loop.run_in_executor(
                None, method_fn, clean, job_dir
            )
            result.runtime_sec = round(time.time() - t0, 2)
            return result

        p2rank_task = asyncio.create_task(_run(run_p2rank, "p2rank"))
        fpocket_task = asyncio.create_task(_run(run_fpocket, "fpocket"))

        results = await asyncio.gather(p2rank_task, fpocket_task)
        job.results = {Method.p2rank: results[0], Method.fpocket: results[1]}
        job.comparison = compare_methods(results[0].pockets, results[1].pockets)

        ligand_center = extract_ligand_center(raw)
        if ligand_center is not None:
            for method, result in job.results.items():
                if not result.error:
                    job.metrics[method] = evaluate_metrics(result, ligand_center)

        job.status = JobStatus.done
    except (PDBNotFoundError, ValueError) as e:
        job.status = JobStatus.failed
        job.error = str(e)
    except Exception as e:
        job.status = JobStatus.failed
        job.error = f"{type(e).__name__}: {e}"
