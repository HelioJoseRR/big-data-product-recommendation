from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def dataset_profile(events: DataFrame) -> dict[str, object]:
    row = events.agg(
        F.count("*").alias("total_events"),
        F.countDistinct("visitorid").alias("total_visitors"),
        F.countDistinct("itemid").alias("total_items"),
        F.sum(F.when(F.col("event") == "transaction", 1).otherwise(0)).alias("total_transactions"),
        F.sum(F.when(F.col("event") == "addtocart", 1).otherwise(0)).alias("total_addtocart"),
        F.sum(F.when(F.col("event") == "view", 1).otherwise(0)).alias("total_views"),
        F.min("timestamp").alias("min_timestamp"),
        F.max("timestamp").alias("max_timestamp"),
    ).first()
    total_events = int(row["total_events"] or 0)
    total_users = int(row["total_visitors"] or 0)
    total_items = int(row["total_items"] or 0)
    possible = total_users * total_items
    sparsity = 1.0 - (total_events / possible) if possible else 0.0
    min_ts = row["min_timestamp"]
    max_ts = row["max_timestamp"]
    dates = events.select(
        F.to_date(F.to_timestamp(F.from_unixtime(F.col("timestamp") / F.lit(1000)))).alias("event_date")
    ).agg(F.min("event_date").alias("event_date_min"), F.max("event_date").alias("event_date_max")).first()
    return {
        **row.asDict(),
        "event_date_min": str(dates["event_date_min"]),
        "event_date_max": str(dates["event_date_max"]),
        "sparsity_estimate": sparsity,
        "avg_events_per_user": total_events / total_users if total_users else 0.0,
        "avg_events_per_item": total_events / total_items if total_items else 0.0,
        "min_timestamp": min_ts,
        "max_timestamp": max_ts,
    }


def write_profile(profile: dict[str, object], metrics_path: Path, report_path: Path) -> None:
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with metrics_path.open("w", encoding="utf-8") as file:
        file.write(",".join(profile.keys()) + "\n")
        file.write(",".join(str(value) for value in profile.values()) + "\n")
    lines = ["# Dataset Profile", ""]
    lines.extend(f"- **{key}**: {value}" for key, value in profile.items())
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
