from __future__ import annotations

import pytest

from retailrocket_recsys.evaluation.ranking_metrics import (
    average_precision_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_top_k_metrics() -> None:
    recommended = [1, 2, 3, 4]
    relevant = [2, 4, 5]

    assert precision_at_k(recommended, relevant, 4) == 0.5
    assert recall_at_k(recommended, relevant, 4) == pytest.approx(2 / 3)
    assert average_precision_at_k(recommended, relevant, 4) == pytest.approx(((1 / 2) + (2 / 4)) / 3)
    assert ndcg_at_k(recommended, relevant, 4) > 0
