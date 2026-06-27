from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from retailrocket_recsys.features import aggregate_interactions


def temporal_cutoff(values: list[int], train_ratio: float) -> int:
    if not values:
        raise ValueError("Cannot compute temporal cutoff for an empty list.")
    ordered = sorted(values)
    index = min(max(int(len(ordered) * train_ratio) - 1, 0), len(ordered) - 1)
    return ordered[index]


def temporal_split_events(events: DataFrame, train_ratio: float) -> tuple[DataFrame, DataFrame, float]:
    cutoff = events.approxQuantile("timestamp", [train_ratio], 0.001)[0]
    train = events.where(F.col("timestamp") <= F.lit(cutoff))
    test = events.where(F.col("timestamp") > F.lit(cutoff))
    return train, test, cutoff


def build_train_test(
    events: DataFrame,
    train_ratio: float,
    use_log_score: bool,
    min_user_interactions: int,
    min_item_interactions: int,
    relevant_events: list[str],
    fallback_relevant_events: list[str],
) -> tuple[DataFrame, DataFrame, DataFrame]:
    train_events, test_events, _ = temporal_split_events(events, train_ratio)
    train_interactions = aggregate_interactions(
        train_events,
        use_log_score=use_log_score,
        min_user_interactions=min_user_interactions,
        min_item_interactions=min_item_interactions,
    )
    test_interactions = aggregate_interactions(
        test_events,
        use_log_score=use_log_score,
        min_user_interactions=1,
        min_item_interactions=1,
    )
    train_users = train_interactions.select("visitorid").distinct()
    relevant = (
        test_events.where(F.col("event").isin(*relevant_events))
        .join(train_users, "visitorid")
        .groupBy("visitorid")
        .agg(F.collect_set("itemid").alias("relevant_items"))
    )
    if relevant.limit(1).count() == 0 and fallback_relevant_events:
        relevant = (
            test_events.where(F.col("event").isin(*fallback_relevant_events))
            .join(train_users, "visitorid")
            .groupBy("visitorid")
            .agg(F.collect_set("itemid").alias("relevant_items"))
        )
    return train_interactions, test_interactions, relevant
