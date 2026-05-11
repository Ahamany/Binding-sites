"""Юнит-тесты для cross-method сравнения карманов."""

import pytest

from app.eval.compare import _euclidean, _jaccard, compare_methods
from app.models.pocket import Pocket


def _pocket(rank: int, center: tuple[float, float, float], residues: list[str]) -> Pocket:
    return Pocket(rank=rank, score=float(rank), center=center, residues=residues)


def test_euclidean_zero():
    assert _euclidean((0, 0, 0), (0, 0, 0)) == 0.0


def test_euclidean_3_4_5():
    assert _euclidean((0, 0, 0), (3, 4, 0)) == pytest.approx(5.0)


def test_jaccard_identical():
    assert _jaccard({"A_1", "A_2"}, {"A_1", "A_2"}) == 1.0


def test_jaccard_disjoint():
    assert _jaccard({"A_1"}, {"A_2"}) == 0.0


def test_jaccard_partial():
    # |∩|=1, |∪|=3 → 1/3
    assert _jaccard({"A_1", "A_2"}, {"A_2", "A_3"}) == pytest.approx(1 / 3)


def test_jaccard_both_empty_is_zero_not_nan():
    """Sanity: пустые множества не должны падать по делению на 0."""
    assert _jaccard(set(), set()) == 0.0


def test_compare_empty_inputs():
    assert compare_methods([], []) == []
    assert compare_methods([_pocket(1, (0, 0, 0), [])], []) == []
    assert compare_methods([], [_pocket(1, (0, 0, 0), [])]) == []


def test_compare_picks_closest_fpocket():
    # P2Rank pocket в (0,0,0). fpocket'ы в (10,0,0) rank=1 и (1,0,0) rank=2.
    # Ближайший — rank=2 (расстояние 1.0), не top-1 fpocket'а.
    p = [_pocket(1, (0, 0, 0), ["A_1"])]
    f = [
        _pocket(1, (10, 0, 0), ["A_99"]),
        _pocket(2, (1, 0, 0), ["A_1"]),
    ]
    matches = compare_methods(p, f)
    assert len(matches) == 1
    m = matches[0]
    assert m.p2rank_rank == 1
    assert m.fpocket_rank == 2     # выбран по дистанции, не по рангу
    assert m.distance == pytest.approx(1.0)
    assert m.jaccard == pytest.approx(1.0)  # обе содержат A_1


def test_compare_one_to_one_per_p2rank():
    """Для каждого P2Rank-кармана ровно один матч; fpocket может повторяться."""
    p = [
        _pocket(1, (0, 0, 0), ["A_1", "A_2"]),
        _pocket(2, (5, 0, 0), ["A_3"]),
    ]
    f = [
        _pocket(1, (0.1, 0.1, 0.1), ["A_1"]),   # ближайший к p[0] и к p[1]? нет
        _pocket(2, (4.9, 0, 0), ["A_3", "A_4"]),
    ]
    matches = compare_methods(p, f)
    assert len(matches) == 2
    assert matches[0].p2rank_rank == 1
    assert matches[0].fpocket_rank == 1
    assert matches[1].p2rank_rank == 2
    assert matches[1].fpocket_rank == 2


def test_compare_jaccard_rounded():
    """Distance и jaccard округляются до 3 знаков."""
    p = [_pocket(1, (0, 0, 0), ["A_1", "A_2", "A_3"])]
    f = [_pocket(1, (1, 1, 1), ["A_1", "A_4", "A_5", "A_6", "A_7"])]
    m = compare_methods(p, f)[0]
    # ∩={A_1}, ∪=7 элементов → 1/7 = 0.142857...
    assert m.jaccard == 0.143
    # sqrt(3) ≈ 1.732
    assert m.distance == 1.732
