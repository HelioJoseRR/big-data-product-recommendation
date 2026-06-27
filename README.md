# RetailRocket Spark Recommender Benchmark

## Objetivo

Implementar uma pipeline local e reproduzivel em Python + Apache Spark para avaliar recomendadores de produtos com o dataset RetailRocket. O projeto gera metricas de qualidade, tempos de execucao, graficos e relatorios para uso em artigo academico.

## Dataset

Baixe o RetailRocket eCommerce Dataset no Kaggle e coloque os CSVs em `data/raw/`:

- `events.csv`
- `item_properties_part1.csv`
- `item_properties_part2.csv`
- `category_tree.csv`

O projeto tambem aceita os CSVs diretamente em `data/`, por compatibilidade com execucoes locais ja existentes. A configuracao padrao usa `data/raw`, mas o codigo faz fallback automatico para `data/` quando os arquivos existem ali.

## Arquitetura da Pipeline

1. Verificacao dos arquivos.
2. Leitura dos CSVs com PySpark.
3. Limpeza, pesos por tipo de evento e agregacao usuario-produto.
4. Split temporal treino/teste.
5. Modelos de popularidade, coocorrencia e ALS.
6. Avaliacao top-k e benchmarks.
7. Geracao de CSVs, PNGs e relatorio Markdown.

## Estrutura do Repositorio

- `src/retailrocket_recsys/`: pipeline, modelos, metricas e CLI.
- `configs/default.yaml`: parametros padrao.
- `data/`: dados brutos, intermediarios e processados.
- `results/`: metricas, figuras e relatorios.
- `docs/`: textos de apoio para o artigo.
- `tests/`: testes automatizados.

## Requisitos

- Python 3.11+
- Java 17
- Apache Spark via PySpark
- Docker opcional

## Execucao com venv

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make check-data
make benchmark-smoke
```

No Windows PowerShell, ative o ambiente com `.venv\Scripts\Activate.ps1`.

## Execucao com Docker

O Docker e o caminho recomendado para evitar diferencas de Java, Spark e sistema operacional.

```bash
docker compose build
docker compose run --rm app make check-data
docker compose run --rm app make benchmark-smoke
docker compose run --rm app make profile
docker compose run --rm app make report
```

Para gerar os Parquets em `data/processed/`, rode:

```bash
docker compose run --rm app make prepare
```

Para uma execucao completa, use:

```bash
docker compose run --rm app make run-all
```

## Comandos Principais

```bash
make check-data
make profile
make prepare
make train-baselines
make train-als
make benchmark-smoke
make benchmark-full
make plot
make report
make run-all
```

Tambem e possivel chamar a CLI diretamente:

```bash
PYTHONPATH=src python -m retailrocket_recsys.cli --help
```

## Benchmarks

O projeto gera comparacoes de modelos, escala por fracao do dataset, particionamento e leitura CSV vs Parquet. O smoke test usa uma fracao reduzida para validar a execucao local.

`make benchmark-smoke` gera metricas, graficos e relatorio em `results/`, mas nao salva os datasets preparados em `data/processed/`. Para preencher `data/processed/`, execute `make prepare`.

## Resultados Gerados

- `results/metrics/dataset_profile.csv`
- `results/metrics/model_benchmark.csv`
- `results/metrics/scale_benchmark.csv`
- `results/metrics/partition_benchmark.csv`
- `results/metrics/storage_benchmark.csv`
- `results/figures/*.png`
- `results/reports/dataset_profile.md`
- `results/reports/experiment_summary.md`

## Dados Processados

A pasta `data/processed/` recebe Parquets quando a etapa `prepare` e executada:

- `events_clean.parquet`: eventos limpos com timestamps e pesos.
- `interactions.parquet`: matriz implicita usuario-produto.
- `train_interactions.parquet`: interacoes de treino.
- `test_interactions.parquet`: interacoes de teste.
- `test_relevant_items.parquet`: itens relevantes por usuario para avaliacao.

## Como Usar os Resultados no Artigo

Use os CSVs para tabelas de metodologia/resultados e os PNGs para comparacoes visuais. O relatorio `experiment_summary.md` resume achados, limitacoes e pontos para discussao.

## Limitacoes

A execucao e local, sem cluster Spark real. O dataset e anonimo, nao possui sessoes explicitas e a avaliacao e offline, portanto ha cold-start e esparsidade.
