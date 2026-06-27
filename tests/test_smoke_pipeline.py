from __future__ import annotations

import pytest

pytest.importorskip("pyspark")

from pyspark.sql import SparkSession
from pyspark.errors import PySparkRuntimeError

from retailrocket_recsys.features import aggregate_interactions
from retailrocket_recsys.preprocessing import clean_events


def test_smoke_pipeline_with_small_dataframe() -> None:
    try:
        spark = SparkSession.builder.master("local[1]").appName("test-smoke").getOrCreate()
    except PySparkRuntimeError as exc:
        pytest.skip(f"Spark JVM unavailable in this environment: {exc}")
    rows = [
        (1000, 1, "view", 10, None),
        (2000, 1, "addtocart", 10, None),
        (3000, 2, "transaction", 11, "t1"),
        (4000, 2, "view", 10, None),
    ]
    df = spark.createDataFrame(rows, ["timestamp", "visitorid", "event", "itemid", "transactionid"])
    cleaned = clean_events(df, {"view": 1.0, "addtocart": 3.0, "transaction": 5.0})
    interactions = aggregate_interactions(cleaned, use_log_score=True, min_user_interactions=1, min_item_interactions=1)

    assert interactions.count() == 3
    assert "score" in interactions.columns
