from __future__ import annotations

from pyspark.ml.recommendation import ALS
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def recommend_als(
    train: DataFrame,
    users: DataFrame,
    k: int,
    rank: int,
    reg_param: float,
    alpha: float,
    max_iter: int,
    implicit_prefs: bool = True,
    nonnegative: bool = True,
    cold_start_strategy: str = "drop",
    exclude_seen: bool = True,
) -> tuple[DataFrame, object]:
    als = ALS(
        userCol="visitorid",
        itemCol="itemid",
        ratingCol="score",
        implicitPrefs=implicit_prefs,
        nonnegative=nonnegative,
        coldStartStrategy=cold_start_strategy,
        rank=rank,
        regParam=reg_param,
        alpha=alpha,
        maxIter=max_iter,
        seed=42,
    )
    model = als.fit(train.select("visitorid", "itemid", "score"))
    recommend_k = k * 5 if exclude_seen else k
    raw_recs = model.recommendForUserSubset(users.select("visitorid").distinct(), recommend_k)
    if not exclude_seen:
        recs = raw_recs.select(
            "visitorid",
            F.expr(f"slice(transform(recommendations, x -> x.itemid), 1, {k})").alias("recommendations"),
        )
        return recs, model

    histories = train.groupBy("visitorid").agg(F.collect_set("itemid").alias("seen_items"))
    recs = raw_recs.join(histories, "visitorid", "left").select(
        "visitorid",
        F.expr(
            f"slice(transform(filter(recommendations, x -> NOT array_contains(seen_items, x.itemid)), "
            f"x -> x.itemid), 1, {k})"
        ).alias("recommendations"),
    )
    return recs, model
