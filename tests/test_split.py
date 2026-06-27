from __future__ import annotations

from retailrocket_recsys.split import temporal_cutoff


def test_temporal_cutoff() -> None:
    assert temporal_cutoff([10, 20, 30, 40, 50], 0.8) == 40
    assert temporal_cutoff([30, 10, 20], 0.5) == 10
