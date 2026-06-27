from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path("results") / ".matplotlib"))

import matplotlib.pyplot as plt
import pandas as pd


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def generate_plots(metrics_dir: Path, figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    scale = _read_csv(metrics_dir / "scale_benchmark.csv")
    partitions = _read_csv(metrics_dir / "partition_benchmark.csv")
    models = _read_csv(metrics_dir / "model_benchmark.csv")
    storage = _read_csv(metrics_dir / "storage_benchmark.csv")

    if not scale.empty:
        plt.figure(figsize=(7, 4))
        plt.plot(scale["fraction"], scale["total_time_seconds"], marker="o", label="tempo total")
        plt.title("Tempo por fracao do dataset")
        plt.xlabel("Fracao")
        plt.ylabel("Segundos")
        plt.legend()
        plt.tight_layout()
        plt.savefig(figures_dir / "runtime_by_fraction.png", dpi=150)
        plt.close()

    if not partitions.empty:
        plt.figure(figsize=(7, 4))
        plt.plot(partitions["partitions"], partitions["total_time_seconds"], marker="o", label="tempo total")
        plt.title("Tempo por numero de particoes")
        plt.xlabel("Particoes")
        plt.ylabel("Segundos")
        plt.legend()
        plt.tight_layout()
        plt.savefig(figures_dir / "runtime_by_partitions.png", dpi=150)
        plt.close()

    if not models.empty:
        plt.figure(figsize=(8, 4))
        x = range(len(models))
        plt.bar([i - 0.2 for i in x], models["precision_at_10"], width=0.4, label="Precision@10")
        plt.bar([i + 0.2 for i in x], models["recall_at_10"], width=0.4, label="Recall@10")
        plt.xticks(list(x), models["model"], rotation=30, ha="right")
        plt.title("Precision e Recall por modelo")
        plt.xlabel("Modelo")
        plt.ylabel("Metrica")
        plt.legend()
        plt.tight_layout()
        plt.savefig(figures_dir / "precision_recall_by_model.png", dpi=150)
        plt.close()

        plt.figure(figsize=(7, 4))
        plt.bar(models["model"], models["coverage"])
        plt.xticks(rotation=30, ha="right")
        plt.title("Coverage por modelo")
        plt.xlabel("Modelo")
        plt.ylabel("Coverage")
        plt.tight_layout()
        plt.savefig(figures_dir / "coverage_by_model.png", dpi=150)
        plt.close()

    if not storage.empty:
        plt.figure(figsize=(6, 4))
        plt.bar(storage["format"], storage["read_time_seconds"])
        plt.title("Leitura CSV vs Parquet")
        plt.xlabel("Formato")
        plt.ylabel("Segundos")
        plt.tight_layout()
        plt.savefig(figures_dir / "storage_csv_vs_parquet.png", dpi=150)
        plt.close()
