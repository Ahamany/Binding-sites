"""Кросс-метод сравнение карманов: P2Rank vs fpocket.

Для каждого кармана P2Rank находим ближайший карман fpocket по евклидову
расстоянию между центрами + считаем Жаккаров коэффициент пересечения резидов.

Это «киллер-метрика» для презентации: если top-1 ↔ top-1 близки (≤5 Å) и
имеют высокий Jaccard — методы согласны на главном сайте.
"""

from math import sqrt

from ..models.pocket import Pocket, PocketMatch


def _euclidean(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def compare_methods(p2rank: list[Pocket], fpocket: list[Pocket]) -> list[PocketMatch]:
    """Для каждого P2Rank-кармана ищем ближайший fpocket-карман.

    Возвращает len(p2rank) или 0 матчей (если один из методов пуст).
    Не симметрично: реверс (fpocket → P2Rank) можно посчитать тривиально, но для
    презентационной таблицы достаточно одной стороны.
    """
    if not p2rank or not fpocket:
        return []

    matches: list[PocketMatch] = []
    for p in p2rank:
        best = min(fpocket, key=lambda f: _euclidean(p.center, f.center))
        matches.append(
            PocketMatch(
                p2rank_rank=p.rank,
                fpocket_rank=best.rank,
                distance=round(_euclidean(p.center, best.center), 3),
                jaccard=round(_jaccard(set(p.residues), set(best.residues)), 3),
            )
        )
    return matches
