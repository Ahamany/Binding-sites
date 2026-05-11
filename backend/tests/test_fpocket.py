"""Unit-тесты на парсеры fpocket info.txt и pocket{N}_atm.pdb.

Fixtures — реальный вывод fpocket 4.0 на 1FBL:
    data/fpocket_1fbl_info.txt
    data/fpocket_1fbl_pocket1_atm.pdb
"""

from pathlib import Path

import pytest

from app.tools.fpocket import parse_info_txt, parse_pocket_atm


DATA = Path(__file__).parent / "data"
INFO = DATA / "fpocket_1fbl_info.txt"
POCKET1 = DATA / "fpocket_1fbl_pocket1_atm.pdb"


def test_info_txt_parses_all_pockets():
    scores = parse_info_txt(INFO)
    assert len(scores) == 19
    assert set(scores.keys()) == set(range(1, 20))


def test_info_txt_top_score_matches():
    scores = parse_info_txt(INFO)
    assert scores[1] == pytest.approx(0.701, rel=1e-3)
    assert scores[2] == pytest.approx(0.184, rel=1e-3)


def test_info_txt_score_descends_overall():
    scores = parse_info_txt(INFO)
    assert scores[1] > scores[19]


def test_pocket_atm_parses_centroid_and_residues():
    center, residues, radius = parse_pocket_atm(POCKET1)

    assert all(isinstance(c, float) for c in center)
    assert radius > 0

    assert len(residues) > 5
    assert all("_" in r for r in residues)
    chains = {r.split("_")[0] for r in residues}
    assert chains == {"A"}


def test_pocket_atm_centroid_in_protein_volume():
    center, _, radius = parse_pocket_atm(POCKET1)
    cx, cy, cz = center
    assert 0 < cx < 200
    assert 0 < cy < 200
    assert -100 < cz < 100
    assert 1.0 < radius < 30.0


def test_pocket_atm_missing_atom_records(tmp_path):
    p = tmp_path / "empty.pdb"
    p.write_text("HEADER fake\nEND\n")
    with pytest.raises(ValueError, match="no ATOM records"):
        parse_pocket_atm(p)


def test_info_txt_handles_blank_lines(tmp_path):
    text = (
        "Pocket 1 :\n"
        "\tScore : \t0.500\n"
        "\tDruggability Score : \t0.100\n"
        "\n"
        "Pocket 2 :\n"
        "\tScore : \t0.300\n"
    )
    p = tmp_path / "info.txt"
    p.write_text(text)
    scores = parse_info_txt(p)
    assert scores == {1: 0.5, 2: 0.3}
