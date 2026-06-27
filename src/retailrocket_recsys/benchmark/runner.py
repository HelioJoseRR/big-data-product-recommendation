from __future__ import annotations

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from pyspark.sql import DataFrame, SparkSession
from retailrocket_recsys.benchmark.timer import Timer
from retailrocket_recsys.config import AppConfig, get_nested
from retailrocket_recsys.data_io import read_events, read_parquet, write_parquet
from retailrocket_recsys.evaluation.evaluator import evaluate_recommendations
from retailrocket_recsys.features import aggregate_interactions, deterministic_user_sample
from retailrocket_recsys.paths import dataset_file, interim_dir, metrics_dir, processed_dir
from retailrocket_recsys.preprocessing import clean_events
from retailrocket_recsys.recommenders.als import recommend_als
from retailrocket_recsys.recommenders.cooccurrence import recommend_cooccurrence
from retailrocket_recsys.recommenders.popularity import recommend_popular
from retailrocket_recsys.split import build_train_test


def run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def append_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_clean_events(config: AppConfig, spark: SparkSession) -> DataFrame:
    weights = get_nested(config, "features", "event_weights", default={})
    events_path = dataset_file(config, get_nested(config, "dataset", "events_file", default="events.csv"))
    return clean_events(read_events(spark, events_path), weights)


def prepare_train_test(
    config: AppConfig,
    events: DataFrame,
    fraction: float,
    partitions: int,
) -> tuple[DataFrame, DataFrame, DataFrame, dict[str, int]]:
    sampled = deterministic_user_sample(events, fraction).repartition(partitions, "visitorid")
    counts = {
        "input_rows": sampled.count(),
        "users": sampled.select("visitorid").distinct().count(),
        "items": sampled.select("itemid").distinct().count(),
    }
    train, test, relevant = build_train_test(
        sampled,
        train_ratio=float(get_nested(config, "split", "train_ratio", default=0.8)),
        use_log_score=bool(get_nested(config, "features", "use_log_score", default=True)),
        min_user_interactions=int(get_nested(config, "features", "min_user_interactions", default=2)),
        min_item_interactions=int(get_nested(config, "features", "min_item_interactions", default=2)),
        relevant_events=list(get_nested(config, "split", "relevant_events", default=["addtocart", "transaction"])),
        fallback_relevant_events=list(get_nested(config, "split", "fallback_relevant_events", default=["view"])),
    )
    return train.cache(), test.cache(), relevant.cache(), counts


def _model_rows(
    config: AppConfig,
    train: DataFrame,
    relevant: DataFrame,
    model_names: Iterable[str],
    fraction: float,
    partitions: int,
    smoke: bool,
    run_identifier: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    k = int(get_nested(config, "recommendation", "k", default=10))
    catalog_items = train.select("itemid").distinct().count()
    train_rows = train.count()
    timestamp = datetime.now(timezone.utc).isoformat()
    users = relevant.select("visitorid").distinct()

    for model_name in model_names:
        model_name = model_name.strip()
        if not model_name:
            continue
        if model_name == "popularity":
            with Timer("train_popularity") as train_timer:
                recommendations = recommend_popular(train, k, bool(get_nested(config, "recommendation", "exclude_seen", default=True)))
            with Timer("evaluate_popularity") as eval_timer:
                metrics = evaluate_recommendations(recommendations, relevant, catalog_items, k)
            total = train_timer.duration_seconds + eval_timer.duration_seconds
            rows.append(_benchmark_row(run_identifier, timestamp, "popularity", fraction, partitions, k, train_rows, catalog_items, train_timer.duration_seconds, 0.0, eval_timer.duration_seconds, total, metrics, "{}"))

        elif model_name == "cooccurrence":
            with Timer("train_cooccurrence") as train_timer:
                recommendations = recommend_cooccurrence(
                    train,
                    k,
                    int(get_nested(config, "recommendation", "max_items_per_user_for_pairs", default=100)),
                    int(get_nested(config, "recommendation", "top_similar_items_per_item", default=50)),
                )
            with Timer("evaluate_cooccurrence") as eval_timer:
                metrics = evaluate_recommendations(recommendations, relevant, catalog_items, k)
            total = train_timer.duration_seconds + eval_timer.duration_seconds
            rows.append(_benchmark_row(run_identifier, timestamp, "cooccurrence", fraction, partitions, k, train_rows, catalog_items, train_timer.duration_seconds, 0.0, eval_timer.duration_seconds, total, metrics, "{}"))

        elif model_name == "als":
            ranks = list(get_nested(config, "als", "ranks", default=[8]))
            regs = list(get_nested(config, "als", "reg_params", default=[0.1]))
            alphas = list(get_nested(config, "als", "alphas", default=[10.0]))
            if smoke:
                ranks, regs, alphas = ranks[:1], regs[:1], alphas[:1]
            for rank in ranks:
                for reg in regs:
                    for alpha in alphas:
                        params = {"rank": rank, "regParam": reg, "alpha": alpha}
                        with Timer("train_als") as train_timer:
                            recommendations, _ = recommend_als(
                                train,
                                users,
                                k,
                                int(rank),
                                float(reg),
                                float(alpha),
                                int(get_nested(config, "als", "max_iter", default=5)),
                                bool(get_nested(config, "als", "implicit_prefs", default=True)),
                                bool(get_nested(config, "als", "nonnegative", default=True)),
                                str(get_nested(config, "als", "cold_start_strategy", default="drop")),
                                bool(get_nested(config, "recommendation", "exclude_seen", default=True)),
                            )
                        with Timer("evaluate_als") as eval_timer:
                            metrics = evaluate_recommendations(recommendations, relevant, catalog_items, k)
                        total = train_timer.duration_seconds + eval_timer.duration_seconds
                        rows.append(_benchmark_row(run_identifier, timestamp, f"als_rank{rank}", fraction, partitions, k, train_rows, catalog_items, train_timer.duration_seconds, 0.0, eval_timer.duration_seconds, total, metrics, json.dumps(params)))
    return rows


def _benchmark_row(
    run_identifier: str,
    timestamp: str,
    model: str,
    fraction: float,
    partitions: int,
    k: int,
    train_rows: int,
    catalog_items: int,
    training_time: float,
    recommendation_time: float,
    evaluation_time: float,
    total_time: float,
    metrics: dict[str, float],
    params: str,
) -> dict[str, object]:
    return {
        "run_id": run_identifier,
        "timestamp": timestamp,
        "model": model,
        "fraction": fraction,
        "partitions": partitions,
        "format": "csv",
        "k": k,
        "train_rows": train_rows,
        "test_users": metrics.get("test_users", 0),
        "catalog_items": catalog_items,
        "training_time_seconds": round(training_time, 4),
        "recommendation_time_seconds": round(recommendation_time, 4),
        "evaluation_time_seconds": round(evaluation_time, 4),
        "total_time_seconds": round(total_time, 4),
        "precision_at_10": metrics.get("precision_at_10", 0.0),
        "recall_at_10": metrics.get("recall_at_10", 0.0),
        "map_at_10": metrics.get("map_at_10", 0.0),
        "ndcg_at_10": metrics.get("ndcg_at_10", 0.0),
        "coverage": metrics.get("coverage", 0.0),
        "params": params,
    }


def run_benchmarks(
    config: AppConfig,
    spark: SparkSession,
    fractions: list[float],
    partitions: list[int],
    models: list[str],
    smoke: bool = False,
) -> None:
    identifier = run_id()
    events = load_clean_events(config, spark).cache()
    selected_partition = partitions[0]
    model_rows: list[dict[str, object]] = []
    scale_rows: list[dict[str, object]] = []
    partition_rows: list[dict[str, object]] = []

    for fraction in fractions:
        start = time.time()
        train, _test, relevant, counts = prepare_train_test(config, events, fraction, selected_partition)
        rows = _model_rows(config, train, relevant, models, fraction, selected_partition, smoke, identifier)
        total = time.time() - start
        model_rows.extend(rows)
        best = rows[-1] if rows else {}
        scale_rows.append({
            "run_id": identifier,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fraction": fraction,
            "input_rows": counts["input_rows"],
            "users": counts["users"],
            "items": counts["items"],
            "partitions": selected_partition,
            "model": best.get("model", ",".join(models)),
            "total_time_seconds": round(total, 4),
            "read_time_seconds": 0.0,
            "preprocessing_time_seconds": 0.0,
            "feature_time_seconds": 0.0,
            "training_time_seconds": best.get("training_time_seconds", 0.0),
            "evaluation_time_seconds": best.get("evaluation_time_seconds", 0.0),
            "precision_at_10": best.get("precision_at_10", 0.0),
            "recall_at_10": best.get("recall_at_10", 0.0),
            "map_at_10": best.get("map_at_10", 0.0),
            "coverage": best.get("coverage", 0.0),
        })
        train.unpersist()
        relevant.unpersist()

    for partition_count in partitions:
        start = time.time()
        train, _test, relevant, counts = prepare_train_test(config, events, fractions[0], partition_count)
        rows = _model_rows(config, train, relevant, ["popularity"], fractions[0], partition_count, True, identifier)
        best = rows[0] if rows else {}
        partition_rows.append({
            "run_id": identifier,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "partitions": partition_count,
            "shuffle_partitions": partition_count,
            "input_rows": counts["input_rows"],
            "aggregation_time_seconds": 0.0,
            "training_time_seconds": best.get("training_time_seconds", 0.0),
            "total_time_seconds": round(time.time() - start, 4),
            "precision_at_10": best.get("precision_at_10", 0.0),
            "recall_at_10": best.get("recall_at_10", 0.0),
            "map_at_10": best.get("map_at_10", 0.0),
            "coverage": best.get("coverage", 0.0),
        })
        train.unpersist()
        relevant.unpersist()

    append_csv(metrics_dir(config) / "model_benchmark.csv", model_rows)
    append_csv(metrics_dir(config) / "scale_benchmark.csv", scale_rows)
    append_csv(metrics_dir(config) / "partition_benchmark.csv", partition_rows)
    append_csv(metrics_dir(config) / "storage_benchmark.csv", storage_benchmark(config, spark, events, identifier))
    events.unpersist()


def storage_benchmark(config: AppConfig, spark: SparkSession, events: DataFrame, identifier: str) -> list[dict[str, object]]:
    events_path = dataset_file(config, get_nested(config, "dataset", "events_file", default="events.csv"))
    parquet_path = interim_dir(config) / "events_storage_benchmark.parquet"
    rows: list[dict[str, object]] = []

    with Timer("read_csv_count") as csv_timer:
        csv_count = read_events(spark, events_path).count()
    rows.append(_storage_row(identifier, "csv", events_path, csv_count, csv_timer.duration_seconds, events_path.stat().st_size))

    try:
        write_parquet(events, parquet_path)
        parquet_size = sum(path.stat().st_size for path in parquet_path.rglob("*") if path.is_file())
        with Timer("read_parquet_count") as parquet_timer:
            parquet_count = read_parquet(spark, parquet_path).count()
        rows.append(
            _storage_row(
                identifier,
                "parquet",
                parquet_path,
                parquet_count,
                parquet_timer.duration_seconds,
                parquet_size,
            )
        )
    except Exception as exc:  # noqa: BLE001
        rows.append(_storage_row(identifier, "parquet", parquet_path, 0, 0.0, 0, str(exc).splitlines()[0]))
    return rows


def _storage_row(
    identifier: str,
    fmt: str,
    path: Path,
    rows: int,
    duration: float,
    size_bytes: int,
    error: str = "",
) -> dict[str, object]:
    return {
        "run_id": identifier,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "format": fmt,
        "input_path": str(path),
        "rows": rows,
        "disk_size_mb": round(size_bytes / (1024 * 1024), 4),
        "read_time_seconds": round(duration, 4),
        "count_time_seconds": round(duration, 4),
        "error": error,
    }


def prepare_outputs(config: AppConfig, spark: SparkSession) -> None:
    events = load_clean_events(config, spark).cache()
    write_parquet(events, processed_dir(config) / "events_clean.parquet")
    interactions = aggregate_interactions(
        events,
        bool(get_nested(config, "features", "use_log_score", default=True)),
        int(get_nested(config, "features", "min_user_interactions", default=2)),
        int(get_nested(config, "features", "min_item_interactions", default=2)),
    )
    write_parquet(interactions, processed_dir(config) / "interactions.parquet")
    train, test, relevant = build_train_test(
        events,
        float(get_nested(config, "split", "train_ratio", default=0.8)),
        bool(get_nested(config, "features", "use_log_score", default=True)),
        int(get_nested(config, "features", "min_user_interactions", default=2)),
        int(get_nested(config, "features", "min_item_interactions", default=2)),
        list(get_nested(config, "split", "relevant_events", default=["addtocart", "transaction"])),
        list(get_nested(config, "split", "fallback_relevant_events", default=["view"])),
    )
    write_parquet(train, processed_dir(config) / "train_interactions.parquet")
    write_parquet(test, processed_dir(config) / "test_interactions.parquet")
    write_parquet(relevant, processed_dir(config) / "test_relevant_items.parquet")
    events.unpersist()
