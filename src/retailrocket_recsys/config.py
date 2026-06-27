from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AppConfig:
    data: dict[str, Any]
    path: Path

    @property
    def random_seed(self) -> int:
        return int(self.data.get("app", {}).get("random_seed", 42))


def load_config(config_path: str | Path = "configs/default.yaml") -> AppConfig:
    path = Path(config_path)
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return AppConfig(data=data, path=path)


def get_nested(config: AppConfig, *keys: str, default: Any = None) -> Any:
    current: Any = config.data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current
