from __future__ import annotations

import shutil
from pathlib import Path

import kagglehub


DATASET = "retailrocket/ecommerce-dataset"
FILES = (
    "events.csv",
    "item_properties_part1.csv",
    "item_properties_part2.csv",
    "category_tree.csv",
)


def main() -> None:
    source_dir = Path(kagglehub.dataset_download(DATASET))
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    for filename in FILES:
        source = source_dir / filename
        destination = raw_dir / filename
        if not source.exists():
            raise FileNotFoundError(f"Arquivo esperado nao encontrado: {source}")
        if destination.exists() or destination.is_symlink():
            destination.unlink()
        shutil.copy2(source, destination)
        print(f"{destination} <- {source}")


if __name__ == "__main__":
    main()
