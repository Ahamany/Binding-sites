"""Unit-тесты на парсер P2Rank predictions CSV.

Fixture `data/p2rank_1fbl_predictions.csv` — реальный вывод P2Rank 2.5.1 на 1FBL.
"""

from pathlib import Path

import pytest

from app.tools.p2rank import parse_predictions_csv


FIXTURE = Path(__file__).parent / "data" / "p2rank_1fbl_predictions.csv"


def test_parses_all_pockets_in_order():
    pockets = parse_predictions_csv(FIXTURE)

    assert len(pockets) == 4
    assert [p.rank for p in pockets] == [1, 2, 3, 4]


def test_top_pocket_score_and_center():
    pockets = parse_predictions_csv(FIXTURE)
    top = pockets[0]

    assert top.score == pytest.approx(9.77, rel=1e-3)
    assert top.center == pytest.approx((70.5274, 83.4375, -11.5099), rel=1e-3)


def test_residue_ids_split_correctly():
    pockets = parse_predictions_csv(FIXTURE)
    top = pockets[0]

    assert top.residues[0] == "A_103"
    assert top.residues[-1] == "A_240"
    assert len(top.residues) == 18
    assert all("_" in r for r in top.residues)


def test_score_monotonic_decreasing():
    pockets = parse_predictions_csv(FIXTURE)
    scores = [p.score for p in pockets]
    assert scores == sorted(scores, reverse=True)


def test_missing_column_raises(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("name,rank,score\npocket1,1,9.0\n")
    with pytest.raises(ValueError, match="missing column 'center_x'"):
        parse_predictions_csv(bad)


def test_empty_csv_returns_empty_list(tmp_path):
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    assert parse_predictions_csv(empty) == []


def test_blank_residue_ids_handled(tmp_path):
    csv_text = (
        "name,rank,score,probability,sas_points,surf_atoms,"
        "center_x,center_y,center_z,residue_ids,surf_atom_ids\n"
        "pocket1,1,5.0,0.3,10,5,1.0,2.0,3.0,,\n"
    )
    p = tmp_path / "no_residues.csv"
    p.write_text(csv_text)
    pockets = parse_predictions_csv(p)
    assert len(pockets) == 1
    assert pockets[0].residues == []
    assert pockets[0].center == (1.0, 2.0, 3.0)
