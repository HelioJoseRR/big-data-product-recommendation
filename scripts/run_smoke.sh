#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=src
python -m retailrocket_recsys.cli benchmark --fractions 0.25 --partitions 4 --models popularity,als --smoke
