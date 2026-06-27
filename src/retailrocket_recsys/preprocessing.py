from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

VALID_EVENTS = ("view", "addtocart", "transaction")


def event_weight_value(event: str, weights: dict[str, float]) -> float:
    return float(weights.get(event, 0.0))


def add_event_weight(df: DataFrame, weights: dict[str, float]) -> DataFrame:
    expression = F.create_map(
        *[item for pair in weights.items() for item in (F.lit(pair[0]), F.lit(float(pair[1])))]
    )
    return df.withColumn("event_weight", expression[F.col("event")].cast("double"))


def clean_events(df: DataFrame, weights: dict[str, float]) -> DataFrame:
    cleaned = (
        df.dropna(subset=["visitorid", "itemid", "timestamp"])
        .where(F.col("event").isin(*VALID_EVENTS))
        .dropDuplicates(["timestamp", "visitorid", "event", "itemid", "transactionid"])
    )
    cleaned = add_event_weight(cleaned, weights)
    return (
        cleaned.withColumn("event_ts", F.to_timestamp(F.from_unixtime(F.col("timestamp") / F.lit(1000))))
        .withColumn("event_date", F.to_date("event_ts"))
        .where(F.col("event_weight").isNotNull())
    )
