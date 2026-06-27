from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from retailrocket_recsys.benchmark.runner import (
    load_clean_events,
    prepare_outputs,
    run_benchmarks,
)
from retailrocket_recsys.config import get_nested, load_config
from retailrocket_recsys.data_io import read_parquet, write_parquet
from retailrocket_recsys.evaluation.evaluator import evaluate_recommendations
from retailrocket_recsys.paths import (
    ensure_project_dirs,
    metrics_dir,
    processed_dir,
    reports_dir,
    required_dataset_files,
)
from retailrocket_recsys.profiling import dataset_profile, write_profile
from retailrocket_recsys.recommenders.als import recommend_als
from retailrocket_recsys.recommenders.cooccurrence import recommend_cooccurrence
from retailrocket_recsys.recommenders.popularity import recommend_popular
from retailrocket_recsys.reporting.markdown_report import generate_report
from retailrocket_recsys.spark import get_spark_session

app = typer.Typer(help="RetailRocket Spark recommender benchmark.")
console = Console()


def _config(config_path: str):
    config = load_config(config_path)
    ensure_project_dirs(config)
    return config


@app.command("check-data")
def check_data(config_path: str = "configs/default.yaml") -> None:
    config = _config(config_path)
    files = required_dataset_files(config)
    table = Table(title="Dataset")
    table.add_column("Arquivo")
    table.add_column("Status")
    missing = []
    for path in files:
        exists = path.exists()
        table.add_row(str(path), "ok" if exists else "faltando")
        if not exists:
            missing.append(path)
    console.print(table)
    if missing:
        console.print(
            "Dataset nao encontrado. Baixe manualmente de "
            "https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset "
            "e coloque os arquivos CSV em data/ ou data/raw/."
        )
        raise typer.Exit(code=1)


@app.command()
def profile(config_path: str = "configs/default.yaml") -> None:
    config = _config(config_path)
    spark = get_spark_session(config)
    events = load_clean_events(config, spark)
    profile_data = dataset_profile(events)
    write_profile(profile_data, metrics_dir(config) / "dataset_profile.csv", reports_dir(config) / "dataset_profile.md")
    console.print("Perfil do dataset gerado em results/metrics e results/reports.")


@app.command()
def prepare(config_path: str = "configs/default.yaml") -> None:
    config = _config(config_path)
    spark = get_spark_session(config)
    prepare_outputs(config, spark)
    console.print("Dados preparados em data/processed.")


@app.command("train-baselines")
def train_baselines(config_path: str = "configs/default.yaml") -> None:
    config = _config(config_path)
    spark = get_spark_session(config)
    train = read_parquet(spark, processed_dir(config) / "train_interactions.parquet")
    k = int(get_nested(config, "recommendation", "k", default=10))
    output_dir = processed_dir(config) / "recommendations"
    output_dir.mkdir(parents=True, exist_ok=True)
    write_parquet(recommend_popular(train, k), output_dir / "popularity.parquet")
    write_parquet(
        recommend_cooccurrence(
            train,
            k,
            int(get_nested(config, "recommendation", "max_items_per_user_for_pairs", default=100)),
            int(get_nested(config, "recommendation", "top_similar_items_per_item", default=50)),
        ),
        output_dir / "cooccurrence.parquet",
    )
    console.print("Recomendacoes baseline salvas em data/processed/recommendations.")


@app.command("train-als")
def train_als(config_path: str = "configs/default.yaml") -> None:
    config = _config(config_path)
    spark = get_spark_session(config)
    train = read_parquet(spark, processed_dir(config) / "train_interactions.parquet")
    relevant = read_parquet(spark, processed_dir(config) / "test_relevant_items.parquet")
    users = relevant.select("visitorid").distinct()
    k = int(get_nested(config, "recommendation", "k", default=10))
    output_dir = processed_dir(config) / "recommendations"
    output_dir.mkdir(parents=True, exist_ok=True)
    for rank in get_nested(config, "als", "ranks", default=[8]):
        recs, _ = recommend_als(
            train,
            users,
            k,
            int(rank),
            float(get_nested(config, "als", "reg_params", default=[0.1])[0]),
            float(get_nested(config, "als", "alphas", default=[10.0])[0]),
            int(get_nested(config, "als", "max_iter", default=5)),
        )
        write_parquet(recs, output_dir / f"als_rank{rank}.parquet")
    console.print("Recomendacoes ALS salvas em data/processed/recommendations.")


@app.command()
def evaluate(config_path: str = "configs/default.yaml") -> None:
    config = _config(config_path)
    spark = get_spark_session(config)
    relevant = read_parquet(spark, processed_dir(config) / "test_relevant_items.parquet")
    train = read_parquet(spark, processed_dir(config) / "train_interactions.parquet")
    catalog_items = train.select("itemid").distinct().count()
    k = int(get_nested(config, "recommendation", "k", default=10))
    rec_path = processed_dir(config) / "recommendations" / "popularity.parquet"
    recs = read_parquet(spark, rec_path)
    metrics = evaluate_recommendations(recs, relevant, catalog_items, k)
    console.print(metrics)


@app.command()
def benchmark(
    config_path: str = "configs/default.yaml",
    fractions: str | None = None,
    partitions: str | None = None,
    models: str | None = None,
    smoke: bool = False,
) -> None:
    config = _config(config_path)
    spark = get_spark_session(config)
    fraction_values = _parse_floats(fractions) or list(get_nested(config, "benchmark", "fractions", default=[0.25]))
    partition_values = _parse_ints(partitions) or list(get_nested(config, "benchmark", "partitions", default=[4]))
    model_values = [m.strip() for m in (models or "popularity,cooccurrence,als").split(",")]
    run_benchmarks(config, spark, fraction_values, partition_values, model_values, smoke)
    from retailrocket_recsys.visualization.plots import generate_plots

    generate_plots(metrics_dir(config), Path(get_nested(config, "paths", "results_dir", default="results")) / "figures")
    generate_report(metrics_dir(config), reports_dir(config))
    console.print("Benchmarks, graficos e relatorio gerados em results/.")


@app.command()
def plot(config_path: str = "configs/default.yaml") -> None:
    config = _config(config_path)
    from retailrocket_recsys.visualization.plots import generate_plots

    generate_plots(metrics_dir(config), Path(get_nested(config, "paths", "results_dir", default="results")) / "figures")
    console.print("Graficos gerados em results/figures.")


@app.command()
def report(config_path: str = "configs/default.yaml") -> None:
    config = _config(config_path)
    output = generate_report(metrics_dir(config), reports_dir(config))
    console.print(f"Relatorio gerado em {output}.")


@app.command("run-all")
def run_all(config_path: str = "configs/default.yaml") -> None:
    profile(config_path)
    prepare(config_path)
    benchmark(config_path=config_path, smoke=True)


def _parse_floats(value: str | None) -> list[float] | None:
    return [float(item.strip()) for item in value.split(",")] if value else None


def _parse_ints(value: str | None) -> list[int] | None:
    return [int(item.strip()) for item in value.split(",")] if value else None


if __name__ == "__main__":
    app()
