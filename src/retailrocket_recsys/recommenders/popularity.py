from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, IntegerType


def recommend_popular(train: DataFrame, k: int, exclude_seen: bool = True, candidate_multiplier: int = 200) -> DataFrame:
    limit = max(k * candidate_multiplier, k)
    popular_items = [
        int(row["itemid"])
        for row in train.groupBy("itemid")
        .agg(F.sum("score").alias("item_score"))
        .orderBy(F.desc("item_score"), F.asc("itemid"))
        .limit(limit)
        .collect()
    ]

    def choose_items(seen_items: list[int] | None) -> list[int]:
        seen = set(seen_items or []) if exclude_seen else set()
        return [item for item in popular_items if item not in seen][:k]

    choose_udf = F.udf(choose_items, ArrayType(IntegerType()))
    users = train.groupBy("visitorid").agg(F.collect_set("itemid").alias("seen_items"))
    return users.select("visitorid", choose_udf("seen_items").alias("recommendations"))
