"""Backend-independent arithmetic; callers establish independent relevance first."""

from math import log2


def recall_and_rr(relevant, ranked, *, k):
    """Existing transcript arithmetic with its nonempty-gold precondition."""
    if type(k) is not int or k < 1 or not relevant:
        raise ValueError("Nonempty relevance set and positive integer k required")
    gold, top = set(relevant), ranked[:k]
    return (
        len(gold.intersection(top)) / len(gold),
        next((1 / r for r, item in enumerate(top, 1) if item in gold), 0.0),
    )


def graded_ranking(grades, pool_grades, *, k):
    """Already deduplicated gains; zero-gain positions are never compressed."""
    if type(k) is not int or not 1 <= k <= 100:
        raise ValueError("k outside evaluation limits")
    if any(type(g) is not int or not 0 <= g <= 3 for g in (*grades, *pool_grades)):
        raise ValueError("grades must be integers in [0,3]")
    dcg = sum((2**g - 1) / log2(r + 1) for r, g in enumerate(grades[:k], 1))
    idcg = sum(
        (2**g - 1) / log2(r + 1)
        for r, g in enumerate(sorted(pool_grades, reverse=True)[:k], 1)
    )
    return dcg, idcg
