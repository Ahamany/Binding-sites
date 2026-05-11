"""Унифицированная схема результатов для всех методов поиска binding sites.

Один формат на выходе у P2Rank, fpocket (и любого будущего метода) даёт нам:
- единый JSON-контракт для фронтенда,
- сравнимую таблицу методов,
- общую функцию метрики (DCC).
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Method(str, Enum):
    p2rank = "p2rank"
    fpocket = "fpocket"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class Pocket(BaseModel):
    """Один предсказанный карман."""

    rank: int = Field(description="1 = top-ranked pocket по методу")
    score: float = Field(description="Скор метода (шкала зависит от метода)")
    center: tuple[float, float, float] = Field(
        description="XYZ центра кармана в системе координат PDB"
    )
    residues: list[str] = Field(
        default_factory=list,
        description="Резиды на стенках кармана, формат 'CHAIN_RESNUM' (например 'A_45')",
    )
    radius: Optional[float] = Field(
        default=None,
        description="Радиус кармана в Å, если метод его выдаёт",
    )


class MethodResult(BaseModel):
    method: Method
    pockets: list[Pocket] = Field(default_factory=list)
    runtime_sec: Optional[float] = None
    error: Optional[str] = None


class Metrics(BaseModel):
    """Метрики оценки. Заполняются только если есть reference site (для бенчмарка)."""

    dcc_top1: Optional[float] = Field(
        default=None,
        description="Distance to Center of Cocrystal ligand для top-1 кармана, Å",
    )
    dcc_top3: Optional[float] = Field(
        default=None,
        description="Минимум DCC по top-3 карманам, Å",
    )
    success_top3: Optional[bool] = Field(
        default=None,
        description="True если хотя бы один из top-3 карманов в пределах 4Å от reference",
    )


class PocketMatch(BaseModel):
    """Соответствие кармана P2Rank → ближайший карман fpocket (по центру)."""

    p2rank_rank: int
    fpocket_rank: int
    distance: float = Field(description="Расстояние между центрами карманов, Å")
    jaccard: float = Field(
        description="Жаккаров коэффициент пересечения резидов (0…1)",
        ge=0.0,
        le=1.0,
    )


class JobCreate(BaseModel):
    """Запрос на создание задачи. Либо pdb_id (fetch с RCSB), либо файл (multipart)."""

    pdb_id: Optional[str] = Field(default=None, pattern=r"^[0-9][A-Za-z0-9]{3}$")


class JobResult(BaseModel):
    """Финальный JSON-ответ для фронта."""

    job_id: str
    status: JobStatus
    pdb_id: Optional[str] = None
    results: dict[Method, MethodResult] = Field(default_factory=dict)
    metrics: dict[Method, Metrics] = Field(default_factory=dict)
    comparison: list[PocketMatch] = Field(
        default_factory=list,
        description="Кросс-метод соответствия P2Rank → fpocket по центрам карманов",
    )
    error: Optional[str] = None
