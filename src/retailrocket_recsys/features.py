from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def aggregate_interactions(
    events: DataFrame,
    use_log_score: bool = True,
    min_user_interactions: int = 1,
    min_item_interactions: int = 1,
) -> DataFrame:
    interactions = events.groupBy("visitorid", "itemid").agg(
        F.sum("event_weight").alias("raw_score"),
        F.count("*").alias("event_count"),
        F.max("event_ts").alias("last_event_ts"),
    )
    score_col = F.log1p("raw_score") if use_log_score else F.col("raw_score")
    interactions = interactions.withColumn("score", score_col.cast("double"))

    user_counts = interactions.groupBy("visitorid").agg(F.count("*").alias("user_interactions"))
    item_counts = interactions.groupBy("itemid").agg(F.count("*").alias("item_interactions"))

    return (
        interactions.join(user_counts, "visitorid")
        .join(item_counts, "itemid")
        .where(F.col("user_interactions") >= min_user_interactions)
        .where(F.col("item_interactions") >= min_item_interactions)
        .select("visitorid", "itemid", "score", "event_count", "last_event_ts")
    )


def deterministic_user_sample(events: DataFrame, fraction: float) -> DataFrame:
    if fraction >= 1.0:
        return events
    threshold = int(fraction * 10000)
    bucket = F.pmod(F.abs(F.hash(F.col("visitorid"))), F.lit(10000))
    return events.where(bucket < threshold)
