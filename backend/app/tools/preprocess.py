"""PDB preprocessing — удаление вод, буферных гетероатомов, фильтрация altloc.

Вход: input.pdb (как пришёл от пользователя или с RCSB).
Выход: clean.pdb, готовый для запуска P2Rank/fpocket.

Что чистим:
- HOH (воды) — обязательно, иначе fpocket будет считать их карманами.
- Буферные ионы и common-cryoprotectants (SO4, PO4, CL, NA, K, MG, ZN, GOL, EDO, ...).
- Altloc != 'A' и != ' ' — берём только основной конформер.

Что НЕ удаляем:
- Native-лиганды (HETATM с произвольным resname, не из BUFFER_RESNAMES) —
  P2Rank сам их игнорирует через `--ignore_ligands` (включено по умолчанию),
  но они полезны как ground truth при DCC-eval.
"""

from pathlib import Path

from Bio.PDB import PDBIO, PDBParser, Select
from Bio.PDB.Structure import Structure


BUFFER_RESNAMES: frozenset[str] = frozenset({
    "HOH", "DOD", "WAT",
    "SO4", "PO4", "CL", "NA", "K", "MG", "ZN", "CA", "FE", "MN", "NI", "CU",
    "GOL", "EDO", "PEG", "PG4", "DMS", "TRS", "MES", "EPE", "ACT", "FMT",
    "BME", "DTT", "IPA", "MPD", "BCT",
})


class _CleanSelect(Select):
    def accept_residue(self, residue) -> bool:
        return residue.get_resname().strip() not in BUFFER_RESNAMES

    def accept_atom(self, atom) -> bool:
        altloc = atom.get_altloc()
        return altloc in ("", " ", "A")


def _parse_pdb(path: Path) -> Structure:
    parser = PDBParser(QUIET=True)
    return parser.get_structure(path.stem, str(path))


def _count_residues(structure: Structure) -> int:
    return sum(1 for _ in structure.get_residues())


def preprocess_pdb(input_path: Path, output_path: Path) -> Path:
    """Очистить PDB-файл перед запуском детекторов.

    Raises:
        ValueError: если после очистки осталось < 20 residues
            (структура битая или не белок).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    structure = _parse_pdb(input_path)
    before = _count_residues(structure)

    io = PDBIO()
    io.set_structure(structure)
    io.save(str(output_path), select=_CleanSelect())

    cleaned = _parse_pdb(output_path)
    after = _count_residues(cleaned)

    if after < 20:
        raise ValueError(
            f"after cleanup only {after} residues left "
            f"(was {before}); structure looks broken"
        )

    return output_path
