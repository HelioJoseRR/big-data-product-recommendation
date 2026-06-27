from __future__ import annotations

from pathlib import Path

import pandas as pd


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _best(df: pd.DataFrame, metric: str) -> str:
    if df.empty or metric not in df:
        return "nao disponivel"
    row = df.sort_values(metric, ascending=False).iloc[0]
    return f"{row.get('model', 'modelo')} ({metric}={row[metric]:.4f})"


def generate_report(metrics_dir: Path, reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    profile = _read(metrics_dir / "dataset_profile.csv")
    models = _read(metrics_dir / "model_benchmark.csv")
    scale = _read(metrics_dir / "scale_benchmark.csv")
    partitions = _read(metrics_dir / "partition_benchmark.csv")
    storage = _read(metrics_dir / "storage_benchmark.csv")

    dataset_lines = ["- Perfil do dataset ainda nao gerado."]
    if not profile.empty:
        first = profile.iloc[0]
        dataset_lines = [
            f"- Total de eventos: {first.get('total_events', 'n/d')}",
            f"- Total de usuarios: {first.get('total_visitors', 'n/d')}",
            f"- Total de itens: {first.get('total_items', 'n/d')}",
            f"- Periodo: {first.get('event_date_min', 'n/d')} a {first.get('event_date_max', 'n/d')}",
            f"- Views: {first.get('total_views', 'n/d')}",
            f"- Add-to-cart: {first.get('total_addtocart', 'n/d')}",
            f"- Transactions: {first.get('total_transactions', 'n/d')}",
        ]

    best_partition = "nao disponivel"
    if not partitions.empty:
        row = partitions.sort_values("total_time_seconds").iloc[0]
        best_partition = f"{row['partitions']} particoes"

    storage_note = "nao disponivel"
    if not storage.empty:
        storage_note = ", ".join(
            f"{row['format']}: {row['read_time_seconds']:.2f}s" for _, row in storage.iterrows()
        )

    content = [
        "# Resumo do Experimento",
        "",
        "## Dataset",
        *dataset_lines,
        "",
        "## Pipeline",
        "- Leitura dos CSVs com schemas explicitos em PySpark.",
        "- Limpeza de eventos invalidos e criacao de pesos implicitos.",
        "- Agregacao usuario-produto, split temporal e avaliacao top-k.",
        "- Modelos: popularidade, coocorrencia item-item e ALS.",
        "",
        "## Benchmarks",
        f"- Modelos avaliados: {', '.join(models['model'].astype(str).tolist()) if not models.empty else 'nao disponivel'}.",
        f"- Fracoes testadas: {', '.join(scale['fraction'].astype(str).tolist()) if not scale.empty else 'nao disponivel'}.",
        f"- Melhor particionamento local: {best_partition}.",
        f"- CSV vs Parquet: {storage_note}.",
        "",
        "## Principais Achados",
        f"- Melhor Precision@10: {_best(models, 'precision_at_10')}.",
        f"- Melhor Recall@10: {_best(models, 'recall_at_10')}.",
        "- Melhor custo-beneficio: comparar qualidade com `total_time_seconds` em `model_benchmark.csv`.",
        f"- Melhor numero de particoes no ambiente local: {best_partition}.",
        "",
        "## Limitacoes",
        "- Execucao local, sem cluster Spark real.",
        "- Dataset anonimizado e sem sessoes explicitas.",
        "- Avaliacao offline sujeita a cold-start e esparsidade.",
        "",
        "## Sugestoes para o Artigo",
        "- Metodologia: descrever pipeline Spark, split temporal e pesos de eventos.",
        "- Resultados: usar tabelas CSV e figuras PNG geradas automaticamente.",
        "- Conclusao: discutir trade-off entre qualidade, tempo e formato de armazenamento.",
    ]
    output = reports_dir / "experiment_summary.md"
    output.write_text("\n".join(content) + "\n", encoding="utf-8")
    return output
