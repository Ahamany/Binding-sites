"""DCC (Distance to Center of Cocrystal) — оценка качества предсказаний.

Идея: у co-crystallized PDB реальный binding-site — это центр лиганда.
DCC top-N = min(distance) от center'ов первых N предсказанных карманов до
центра лиганда. Успех — если DCC ≤ 4 Å (стандарт P2Rank-paper / COACH420).

extract_ligand_center ходит по ОРИГИНАЛЬНОМУ PDB (до preprocess'а), выбирает
самую крупную HETATM-группу не из BUFFER_RESNAMES (исключая воду, буферы,
cryoprotectants) и возвращает её центроид.
"""

from __future__ import annotations

from math import sqrt
from pathlib import Path
from typing import Optional

from Bio.PDB import PDBParser

from ..models.pocket import MethodResult, Metrics
from ..tools.preprocess import BUFFER_RESNAMES


SUCCESS_THRESHOLD_A = 4.0


def compute_dcc(
    pocket_center: tuple[float, float, float],
    ligand_center: tuple[float, float, float],
) -> float:
    """Евклидово расстояние между двумя точками XYZ, Å."""
    return sqrt(
        (pocket_center[0] - ligand_center[0]) ** 2
        + (pocket_center[1] - ligand_center[1]) ** 2
        + (pocket_center[2] - ligand_center[2]) ** 2
    )


def extract_ligand_center(
    pdb_path: Path,
    resname_override: Optional[str] = None,
) -> Optional[tuple[float, float, float]]:
    """Извлечь центр co-crystallized лиганда из ОРИГИНАЛЬНОГО PDB.

    Алгоритм:
        1. Парсим PDB.
        2. Берём только HETATM (residue.id[0] != " ").
        3. Исключаем BUFFER_RESNAMES (воды, ионы, cryoprotectants).
        4. Если задан resname_override — оставляем только residue с этим resname.
        5. Среди оставшихся выбираем группу (один Residue) с max числом атомов.
        6. Возвращаем центроид (среднее по координатам атомов).

    Returns None если не нашли подходящих HETATM или PDB не парсится.
    """
    parser = PDBParser(QUIET=True)
    try:
        structure = parser.get_structure(pdb_path.stem, str(pdb_path))
    except Exception:
        return None

    best_atoms: list[tuple[float, float, float]] = []

    for residue in structure.get_residues():
        hetflag = residue.id[0]
        if hetflag == " ":
            continue
        resname = residue.get_resname().strip()
        if resname in BUFFER_RESNAMES:
            continue
        if resname_override and resname != resname_override.strip():
            continue
        atoms = [
            (float(a.coord[0]), float(a.coord[1]), float(a.coord[2]))
            for a in residue.get_atoms()
        ]
        if len(atoms) > len(best_atoms):
            best_atoms = atoms

    if not best_atoms:
        return None

    n = len(best_atoms)
    cx = sum(a[0] for a in best_atoms) / n
    cy = sum(a[1] for a in best_atoms) / n
    cz = sum(a[2] for a in best_atoms) / n
    return (cx, cy, cz)


def evaluate_metrics(
    method_result: MethodResult,
    ligand_center: tuple[float, float, float],
    *,
    success_threshold: float = SUCCESS_THRESHOLD_A,
) -> Metrics:
    """DCC top-1 / top-3 + success_top3 для одного метода.

    - dcc_top1 = DCC(top-1 pocket, ligand)
    - dcc_top3 = min(DCC) среди top-3 карманов (≤3 если меньше карманов)
    - success_top3 = (dcc_top3 ≤ threshold)

    Пустой pockets → dcc_*=None, success_top3=False ("метод не нашёл ничего").
    """
    pockets = method_result.pockets
    if not pockets:
        return Metrics(dcc_top1=None, dcc_top3=None, success_top3=False)

    pockets_sorted = sorted(pockets, key=lambda p: p.rank)
    dcc_values = [compute_dcc(p.center, ligand_center) for p in pockets_sorted[:3]]

    dcc_top1 = round(dcc_values[0], 3)
    dcc_top3 = round(min(dcc_values), 3)
    return Metrics(
        dcc_top1=dcc_top1,
        dcc_top3=dcc_top3,
        success_top3=dcc_top3 <= success_threshold,
    )
