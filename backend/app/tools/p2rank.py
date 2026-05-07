"""P2Rank wrapper — Day 2 deliverable.

Текущее состояние: stub. Полная реализация — день 2 по плану.

Спецификация:
    P2Rank вызывается как `prank predict -f input.pdb -o out_dir`.
    Результат — CSV в out_dir/input.pdb_predictions.csv с колонками:
        name, rank, score, probability, sas_points, surf_atoms,
        center_x, center_y, center_z, residue_ids, surf_atom_ids

Парсер должен вернуть list[Pocket] с заполненными rank, score, center, residues.
"""

from pathlib import Path

from ..models.pocket import MethodResult, Method


def run_p2rank(pdb_path: Path, work_dir: Path) -> MethodResult:
    """Запустить P2Rank на PDB-файле и вернуть унифицированный результат.

    TODO (день 2):
    - subprocess вызов `prank predict -f {pdb_path} -o {work_dir}`
    - парсинг CSV-файла с предсказаниями
    - конвертация в list[Pocket]
    """
    return MethodResult(
        method=Method.p2rank,
        pockets=[],
        error="not implemented yet (Day 2 task)",
    )
