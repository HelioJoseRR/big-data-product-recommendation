from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

from retailrocket_recsys.evaluation.ranking_metrics import (
    average_precision_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def evaluate_recommendations(recommendations: DataFrame, relevant_items: DataFrame, catalog_items: int, k: int) -> dict[str, float]:
    joined = recommendations.join(relevant_items, "visitorid", "inner").where(F.size("relevant_items") > 0)
    precision_udf = F.udf(lambda rec, rel: precision_at_k(rec or [], rel or [], k), DoubleType())
    recall_udf = F.udf(lambda rec, rel: recall_at_k(rec or [], rel or [], k), DoubleType())
    map_udf = F.udf(lambda rec, rel: average_precision_at_k(rec or [], rel or [], k), DoubleType())
    ndcg_udf = F.udf(lambda rec, rel: ndcg_at_k(rec or [], rel or [], k), DoubleType())

    scored = (
        joined.withColumn(f"precision_at_{k}", precision_udf("recommendations", "relevant_items"))
        .withColumn(f"recall_at_{k}", recall_udf("recommendations", "relevant_items"))
        .withColumn(f"map_at_{k}", map_udf("recommendations", "relevant_items"))
        .withColumn(f"ndcg_at_{k}", ndcg_udf("recommendations", "relevant_items"))
    )
    aggregate = scored.agg(
        F.avg(f"precision_at_{k}").alias(f"precision_at_{k}"),
        F.avg(f"recall_at_{k}").alias(f"recall_at_{k}"),
        F.avg(f"map_at_{k}").alias(f"map_at_{k}"),
        F.avg(f"ndcg_at_{k}").alias(f"ndcg_at_{k}"),
        F.count("*").alias("test_users"),
    ).first()
    recommended_items = recommendations.select(F.explode("recommendations").alias("itemid")).distinct().count()
    coverage = recommended_items / catalog_items if catalog_items else 0.0
    values = aggregate.asDict() if aggregate else {}
    return {
        f"precision_at_{k}": float(values.get(f"precision_at_{k}") or 0.0),
        f"recall_at_{k}": float(values.get(f"recall_at_{k}") or 0.0),
        f"map_at_{k}": float(values.get(f"map_at_{k}") or 0.0),
        f"ndcg_at_{k}": float(values.get(f"ndcg_at_{k}") or 0.0),
        "coverage": float(coverage),
        "test_users": int(values.get("test_users") or 0),
    }
