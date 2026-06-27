from __future__ import annotations

import math

from retailrocket_recsys.preprocessing import event_weight_value


def test_event_weight_value() -> None:
    weights = {"view": 1.0, "addtocart": 3.0, "transaction": 5.0}

    assert event_weight_value("view", weights) == 1.0
    assert event_weight_value("addtocart", weights) == 3.0
    assert event_weight_value("transaction", weights) == 5.0
    assert event_weight_value("unknown", weights) == 0.0


def test_log_score_rule() -> None:
    assert math.log1p(5.0) > math.log1p(1.0)
