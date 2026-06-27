from __future__ import annotations

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def recommend_cooccurrence(
    train: DataFrame,
    k: int,
    max_items_per_user_for_pairs: int = 100,
    top_similar_items_per_item: int = 50,
) -> DataFrame:
    histories = train.groupBy("visitorid").agg(F.collect_set("itemid").alias("seen_items"))
    bounded = histories.where(F.size("seen_items") <= max_items_per_user_for_pairs)
    pairs = (
        bounded.select("visitorid", F.explode("seen_items").alias("itemid"), "seen_items")
        .select("itemid", F.explode("seen_items").alias("candidate_itemid"))
        .where(F.col("itemid") != F.col("candidate_itemid"))
    )
    similarities = pairs.groupBy("itemid", "candidate_itemid").agg(F.count("*").alias("similarity"))
    window = Window.partitionBy("itemid").orderBy(F.desc("similarity"), F.asc("candidate_itemid"))
    top_similar = (
        similarities.withColumn("rank", F.row_number().over(window))
        .where(F.col("rank") <= top_similar_items_per_item)
        .drop("rank")
    )
    scores = (
        histories.select("visitorid", "seen_items", F.explode("seen_items").alias("itemid"))
        .join(top_similar, "itemid")
        .where(~F.array_contains(F.col("seen_items"), F.col("candidate_itemid")))
        .groupBy("visitorid", "candidate_itemid")
        .agg(F.sum("similarity").alias("score"))
    )
    user_window = Window.partitionBy("visitorid").orderBy(F.desc("score"), F.asc("candidate_itemid"))
    ranked = scores.withColumn("rank", F.row_number().over(user_window)).where(F.col("rank") <= k)
    return ranked.groupBy("visitorid").agg(
        F.expr("transform(sort_array(collect_list(struct(rank, candidate_itemid))), x -> x.candidate_itemid)").alias(
            "recommendations"
        )
    )
