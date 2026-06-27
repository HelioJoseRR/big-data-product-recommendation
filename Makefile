.PHONY: install lint test check-data profile prepare train-baselines train-als evaluate benchmark-smoke benchmark-full plot report run-all clean

export PYTHONPATH := src

install:
	pip install -r requirements.txt

lint:
	ruff check src tests

test:
	pytest -q

check-data:
	PYTHONPATH=src python -m retailrocket_recsys.cli check-data

profile:
	PYTHONPATH=src python -m retailrocket_recsys.cli profile

prepare:
	PYTHONPATH=src python -m retailrocket_recsys.cli prepare

train-baselines:
	PYTHONPATH=src python -m retailrocket_recsys.cli train-baselines

train-als:
	PYTHONPATH=src python -m retailrocket_recsys.cli train-als

evaluate:
	PYTHONPATH=src python -m retailrocket_recsys.cli evaluate

benchmark-smoke:
	PYTHONPATH=src python -m retailrocket_recsys.cli benchmark --fractions 0.25 --partitions 4 --models popularity,als --smoke

benchmark-full:
	PYTHONPATH=src python -m retailrocket_recsys.cli benchmark

plot:
	PYTHONPATH=src python -m retailrocket_recsys.cli plot

report:
	PYTHONPATH=src python -m retailrocket_recsys.cli report

run-all:
	PYTHONPATH=src python -m retailrocket_recsys.cli run-all

clean:
	rm -rf data/interim/* data/processed/* results/metrics/* results/figures/* results/reports/*
