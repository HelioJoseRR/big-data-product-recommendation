from __future__ import annotations

from pathlib import Path

from retailrocket_recsys.config import AppConfig, get_nested


def project_root() -> Path:
    return Path.cwd()


def resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else project_root() / candidate


def ensure_dir(path: str | Path) -> Path:
    resolved = resolve_path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def ensure_project_dirs(config: AppConfig) -> None:
    for key in ("raw_dir", "interim_dir", "processed_dir"):
        ensure_dir(get_nested(config, "paths", key))
    results_dir = ensure_dir(get_nested(config, "paths", "results_dir"))
    for child in ("metrics", "figures", "reports"):
        ensure_dir(results_dir / child)


def raw_dir(config: AppConfig) -> Path:
    return resolve_path(get_nested(config, "paths", "raw_dir", default="data"))


def processed_dir(config: AppConfig) -> Path:
    return ensure_dir(get_nested(config, "paths", "processed_dir", default="data/processed"))


def interim_dir(config: AppConfig) -> Path:
    return ensure_dir(get_nested(config, "paths", "interim_dir", default="data/interim"))


def results_dir(config: AppConfig) -> Path:
    return ensure_dir(get_nested(config, "paths", "results_dir", default="results"))


def metrics_dir(config: AppConfig) -> Path:
    return ensure_dir(results_dir(config) / "metrics")


def figures_dir(config: AppConfig) -> Path:
    return ensure_dir(results_dir(config) / "figures")


def reports_dir(config: AppConfig) -> Path:
    return ensure_dir(results_dir(config) / "reports")


def dataset_file(config: AppConfig, filename: str) -> Path:
    primary = raw_dir(config) / filename
    if primary.exists():
        return primary
    fallback = resolve_path("data") / filename
    if fallback.exists():
        return fallback
    raw_fallback = resolve_path("data/raw") / filename
    if raw_fallback.exists():
        return raw_fallback
    return primary


def required_dataset_files(config: AppConfig) -> list[Path]:
    events = get_nested(config, "dataset", "events_file", default="events.csv")
    category = get_nested(config, "dataset", "category_tree_file", default="category_tree.csv")
    item_files = get_nested(config, "dataset", "item_properties_files", default=[])
    filenames = [events, *item_files, category]
    return [dataset_file(config, name) for name in filenames]
