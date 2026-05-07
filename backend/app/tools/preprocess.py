"""PDB preprocessing — удаление вод, гетероатомов, фильтрация.

Минимальная реализация для скелета: pass-through copy.
Полная реализация — день 2–3 (BioPython-based cleanup).
"""

import shutil
from pathlib import Path


def preprocess_pdb(input_path: Path, output_path: Path) -> Path:
    """Очистить PDB-файл перед запуском детекторов.

    TODO (день 2):
    - удалить HOH (воды), buffer ions (SO4, CL, NA, ...)
    - оставить только altloc='A' если есть несколько
    - проверить sanity: число residues > 20

    Сейчас просто копирует файл.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(input_path, output_path)
    return output_path
