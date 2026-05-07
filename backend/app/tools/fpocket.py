"""fpocket wrapper — Day 3 deliverable.

Текущее состояние: stub.

Спецификация:
    fpocket вызывается как `fpocket -f input.pdb`.
    Результат — папка input_out/ с:
        - input_info.txt — табличный summary по всем pocket'ам
        - pockets/pocket{N}_atm.pdb — атомы кармана N
        - pockets/pocket{N}_vert.pqr — вершины Voronoi-сферы

Парсер должен прочитать info.txt и pockets/*_atm.pdb, выдать list[Pocket].
"""

from pathlib import Path

from ..models.pocket import MethodResult, Method


def run_fpocket(pdb_path: Path, work_dir: Path) -> MethodResult:
    """Запустить fpocket на PDB-файле и вернуть унифицированный результат.

    TODO (день 3):
    - копировать pdb_path в work_dir, потому что fpocket пишет рядом со входом
    - subprocess вызов `fpocket -f {work_dir}/input.pdb`
    - парсинг info.txt
    - вычисление центра кармана из pocket{N}_atm.pdb (среднее по координатам)
    - конвертация в list[Pocket]
    """
    return MethodResult(
        method=Method.fpocket,
        pockets=[],
        error="not implemented yet (Day 3 task)",
    )
