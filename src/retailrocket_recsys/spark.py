from __future__ import annotations

from pathlib import Path

from pyspark.sql import SparkSession

from retailrocket_recsys.config import AppConfig, get_nested


def get_spark_session(config: AppConfig, master: str | None = None) -> SparkSession:
    spark_conf = get_nested(config, "spark", default={})
    local_dir = Path(spark_conf.get("local_dir", "data/interim/spark-local"))
    local_dir.mkdir(parents=True, exist_ok=True)
    builder = (
        SparkSession.builder.master(master or spark_conf.get("master", "local[*]"))
        .appName(spark_conf.get("app_name", "RetailRocketSparkRecommender"))
        .config("spark.driver.memory", spark_conf.get("driver_memory", "4g"))
        .config("spark.sql.shuffle.partitions", str(spark_conf.get("shuffle_partitions", 8)))
        .config("spark.sql.adaptive.enabled", str(spark_conf.get("adaptive_enabled", True)).lower())
        .config("spark.local.dir", str(local_dir.resolve()))
    )
    for key, value in spark_conf.get("extra_conf", {}).items():
        builder = builder.config(key, str(value))
    return builder.getOrCreate()
