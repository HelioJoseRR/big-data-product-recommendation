from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import IntegerType, LongType, StringType, StructField, StructType


EVENTS_SCHEMA = StructType(
    [
        StructField("timestamp", LongType(), True),
        StructField("visitorid", IntegerType(), True),
        StructField("event", StringType(), True),
        StructField("itemid", IntegerType(), True),
        StructField("transactionid", StringType(), True),
    ]
)

ITEM_PROPERTIES_SCHEMA = StructType(
    [
        StructField("timestamp", LongType(), True),
        StructField("itemid", IntegerType(), True),
        StructField("property", StringType(), True),
        StructField("value", StringType(), True),
    ]
)

CATEGORY_TREE_SCHEMA = StructType(
    [
        StructField("categoryid", IntegerType(), True),
        StructField("parentid", IntegerType(), True),
    ]
)


def read_events(spark: SparkSession, path: str | Path) -> DataFrame:
    return spark.read.csv(str(path), header=True, schema=EVENTS_SCHEMA)


def read_item_properties(spark: SparkSession, paths: list[str | Path]) -> DataFrame:
    return spark.read.csv([str(path) for path in paths], header=True, schema=ITEM_PROPERTIES_SCHEMA)


def read_category_tree(spark: SparkSession, path: str | Path) -> DataFrame:
    return spark.read.csv(str(path), header=True, schema=CATEGORY_TREE_SCHEMA)


def write_parquet(df: DataFrame, path: str | Path, mode: str = "overwrite") -> None:
    df.write.mode(mode).parquet(str(path))


def read_parquet(spark: SparkSession, path: str | Path) -> DataFrame:
    return spark.read.parquet(str(path))
