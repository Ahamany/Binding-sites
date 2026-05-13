"""Юнит-тесты для DCC-метрики и извлечения co-crystallized ligand'а."""

from pathlib import Path

import pytest

from app.eval.dcc import (
    SUCCESS_THRESHOLD_A,
    compute_dcc,
    evaluate_metrics,
    extract_ligand_center,
)
from app.models.pocket import Method, MethodResult, Pocket


def _pocket(rank: int, center: tuple[float, float, float]) -> Pocket:
    return Pocket(rank=rank, score=float(rank), center=center, residues=[])


def _result(pockets: list[Pocket]) -> MethodResult:
    return MethodResult(method=Method.p2rank, pockets=pockets)


def _atom(
    serial: int,
    atom_name: str,
    resname: str,
    chain: str,
    resseq: int,
    x: float,
    y: float,
    z: float,
    *,
    hetatm: bool = False,
) -> str:
    """Собрать одну ATOM/HETATM PDB-строку по spec (cols 1–78)."""
    record = "HETATM" if hetatm else "ATOM  "
    name_field = f" {atom_name:<3s}"   # cols 13–16 (один пробел + до 3 символов)
    element = atom_name[0]
    return (
        f"{record}"                     # 1–6
        f"{serial:>5d}"                 # 7–11
        f" "                            # 12
        f"{name_field}"                 # 13–16
        f" "                            # 17 (altLoc)
        f"{resname:>3s}"                # 18–20
        f" "                            # 21
        f"{chain:1s}"                   # 22
        f"{resseq:>4d}"                 # 23–26
        f"    "                         # 27–30
        f"{x:>8.3f}{y:>8.3f}{z:>8.3f}"  # 31–54
        f"  1.00  0.00          "       # 55–76
        f" {element}"                   # 77–78
    )


def _write_pdb(tmp_path: Path, name: str, lines: list[str]) -> Path:
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\nEND\n")
    return path


# ---- compute_dcc --------------------------------------------------------------

def test_compute_dcc_known_3_4_5():
    assert compute_dcc((0, 0, 0), (3, 4, 0)) == pytest.approx(5.0)


def test_compute_dcc_identical():
    assert compute_dcc((1.5, -2.0, 3.3), (1.5, -2.0, 3.3)) == 0.0


# ---- evaluate_metrics ---------------------------------------------------------

def test_evaluate_metrics_empty_pockets():
    m = evaluate_metrics(_result([]), (0.0, 0.0, 0.0))
    assert m.dcc_top1 is None
    assert m.dcc_top3 is None
    assert m.success_top3 is False


def test_evaluate_metrics_success_at_threshold():
    # Top-1 ровно на 4.0 Å от лиганда — должно быть success.
    p = _pocket(1, (SUCCESS_THRESHOLD_A, 0.0, 0.0))
    m = evaluate_metrics(_result([p]), (0.0, 0.0, 0.0))
    assert m.dcc_top1 == SUCCESS_THRESHOLD_A
    assert m.dcc_top3 == SUCCESS_THRESHOLD_A
    assert m.success_top3 is True


def test_evaluate_metrics_above_threshold_is_failure():
    p = _pocket(1, (SUCCESS_THRESHOLD_A + 0.01, 0.0, 0.0))
    m = evaluate_metrics(_result([p]), (0.0, 0.0, 0.0))
    assert m.success_top3 is False


def test_evaluate_metrics_top3_takes_minimum():
    # pocket #3 ближе к лиганду, чем #1 → top3 < top1.
    pockets = [
        _pocket(1, (10.0, 0.0, 0.0)),   # DCC 10
        _pocket(2, (8.0, 0.0, 0.0)),    # DCC 8
        _pocket(3, (2.0, 0.0, 0.0)),    # DCC 2
    ]
    m = evaluate_metrics(_result(pockets), (0.0, 0.0, 0.0))
    assert m.dcc_top1 == 10.0
    assert m.dcc_top3 == 2.0
    assert m.success_top3 is True


def test_evaluate_metrics_only_considers_top3():
    # 4-й карман ближе всех, но в top-3 мы его не должны учитывать.
    pockets = [
        _pocket(1, (10.0, 0.0, 0.0)),
        _pocket(2, (10.0, 0.0, 0.0)),
        _pocket(3, (10.0, 0.0, 0.0)),
        _pocket(4, (0.5, 0.0, 0.0)),    # ближе, но #4 — за пределами top-3
    ]
    m = evaluate_metrics(_result(pockets), (0.0, 0.0, 0.0))
    assert m.dcc_top3 == 10.0
    assert m.success_top3 is False


# ---- extract_ligand_center ----------------------------------------------------

def test_extract_ligand_center_inline_pdb(tmp_path):
    pdb = _write_pdb(tmp_path, "lig.pdb", [
        _atom(1, "N",  "ALA", "A", 1, 0.0,  0.0,  0.0),
        _atom(2, "CA", "ALA", "A", 1, 1.5,  0.0,  0.0),
        _atom(3, "C1", "LIG", "A", 100, 10.0, 10.0, 10.0, hetatm=True),
        _atom(4, "C2", "LIG", "A", 100, 14.0, 10.0, 10.0, hetatm=True),
    ])
    center = extract_ligand_center(pdb)
    assert center is not None
    assert center == pytest.approx((12.0, 10.0, 10.0), abs=1e-3)


def test_extract_ligand_center_no_hetatm(tmp_path):
    pdb = _write_pdb(tmp_path, "apo.pdb", [
        _atom(1, "N",  "ALA", "A", 1, 0.0, 0.0, 0.0),
        _atom(2, "CA", "ALA", "A", 1, 1.5, 0.0, 0.0),
    ])
    assert extract_ligand_center(pdb) is None


def test_extract_ligand_center_skips_buffer_resnames(tmp_path):
    pdb = _write_pdb(tmp_path, "buffers.pdb", [
        _atom(1, "N",  "ALA", "A", 1, 0.0, 0.0, 0.0),
        _atom(2, "O",  "HOH", "A", 200, 5.0,  5.0,  5.0,  hetatm=True),
        _atom(3, "S",  "SO4", "A", 201, 10.0, 10.0, 10.0, hetatm=True),
        _atom(4, "MG", "MG",  "A", 202, 15.0, 15.0, 15.0, hetatm=True),
    ])
    assert extract_ligand_center(pdb) is None


def test_extract_ligand_center_picks_largest_group(tmp_path):
    # SML: 1 атом, BIG: 3 атома → выбран BIG, центроид ≈ (10.667, 10.667, 10.0).
    pdb = _write_pdb(tmp_path, "two_lig.pdb", [
        _atom(1, "N",  "ALA", "A", 1, 0.0, 0.0, 0.0),
        _atom(2, "C1", "SML", "A", 100, 1.0, 1.0, 1.0,    hetatm=True),
        _atom(3, "C1", "BIG", "A", 200, 10.0, 10.0, 10.0, hetatm=True),
        _atom(4, "C2", "BIG", "A", 200, 12.0, 10.0, 10.0, hetatm=True),
        _atom(5, "C3", "BIG", "A", 200, 10.0, 12.0, 10.0, hetatm=True),
    ])
    center = extract_ligand_center(pdb)
    assert center is not None
    expected_xy = (10.0 + 12.0 + 10.0) / 3
    assert center == pytest.approx((expected_xy, expected_xy, 10.0), abs=1e-3)


def test_extract_ligand_center_override_picks_named_resname(tmp_path):
    # Без override победит BIG (3 атома). С override="SML" — берём только SML.
    pdb = _write_pdb(tmp_path, "override.pdb", [
        _atom(1, "N",  "ALA", "A", 1, 0.0, 0.0, 0.0),
        _atom(2, "S1", "SML", "A", 100, 5.0, 5.0, 5.0,    hetatm=True),
        _atom(3, "B1", "BIG", "A", 200, 50.0, 50.0, 50.0, hetatm=True),
        _atom(4, "B2", "BIG", "A", 200, 52.0, 50.0, 50.0, hetatm=True),
        _atom(5, "B3", "BIG", "A", 200, 50.0, 52.0, 50.0, hetatm=True),
    ])
    center = extract_ligand_center(pdb, resname_override="SML")
    assert center is not None
    assert center == pytest.approx((5.0, 5.0, 5.0), abs=1e-3)


def test_extract_ligand_center_returns_none_on_malformed(tmp_path):
    bad = tmp_path / "bad.pdb"
    bad.write_text("\x00\x01not a pdb\x02\n")
    # BioPython либо парсит как пустую структуру, либо бросает — оба → None.
    assert extract_ligand_center(bad) is None
