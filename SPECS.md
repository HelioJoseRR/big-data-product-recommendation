# SPECS.md — RetailRank

## Projeto

**RetailRank: Pipeline Big Data com Apache Spark para Recomendação de Produtos em E-commerce**

Este documento organiza as especificações incrementais de implementação. A base de dados deve ficar em `./data/raw`, e o processamento principal deve ser feito com Apache Spark. Pandas só deve ser usado para visualização ou leitura de pequenos artefatos finais.

## SPEC-00 — Setup Inicial

**Objetivo:** criar estrutura, dependências e comandos básicos.

**Arquivos esperados:**

```text
data/raw/
data/bronze/
data/silver/
data/gold/
outputs/metrics/
outputs/recommendations/
outputs/figures/
src/__init__.py
src/config.py
src/spark_session.py
experiments/
tests/
requirements.txt
Makefile
Dockerfile
docker-compose.yml
README.md
```

**Dependências mínimas:** `pyspark`, `fastapi`, `uvicorn`, `streamlit`, `matplotlib`, `pytest`, `python-dotenv`.

**Aceite:** estrutura criada, `make install` e `make test` disponíveis, README inicial com objetivo e instruções.

## SPEC-01 — Configuração e SparkSession

**Objetivo:** centralizar paths e criação da SparkSession.

**Arquivos:** `src/config.py`, `src/spark_session.py`, `tests/test_spark_session.py`.

**Constantes mínimas:** `RAW_DATA_PATH`, `BRONZE_DATA_PATH`, `SILVER_DATA_PATH`, `GOLD_DATA_PATH`, `OUTPUT_METRICS_PATH`, `OUTPUT_RECOMMENDATIONS_PATH`.

**Função obrigatória:** `get_spark(app_name: str)`.

**Aceite:** SparkSession válida com timezone UTC, shuffle partitions configurável, adaptive query execution habilitado e log level reduzido.

## SPEC-02 — Ingestão Raw -> Bronze

**Objetivo:** ler `./data/raw/*.csv` e salvar Parquet em `./data/bronze/events`.

**Arquivo:** `src/ingestion.py`.

**Schema:** `event_time`, `event_type`, `product_id`, `category_id`, `category_code`, `brand`, `price`, `user_id`, `user_session`.

**Requisitos:** schema explícito, colunas `source_file` e `ingestion_timestamp`, métricas de tempo e linhas em `outputs/metrics/ingestion_metrics.json`.

**Comando:** `make ingest` ou `python -m src.ingestion`.

## SPEC-03 — Limpeza Bronze -> Silver

**Objetivo:** criar `./data/silver/events` limpo, tipado e particionado.

**Arquivo:** `src/preprocessing.py`.

**Transformações:** converter tipos, criar `event_date`, `event_year`, `event_month`, `event_day`, `event_hour`; filtrar nulos e `price < 0`; manter apenas `view`, `cart`, `remove_from_cart`, `purchase`.

**Particionamento:** `event_month`, `event_type`.

**Métricas:** `outputs/metrics/preprocessing_metrics.json`.

## SPEC-04 — Camada Gold

**Objetivo:** gerar agregações para análise e recomendação.

**Arquivo:** `src/feature_engineering.py`.

**Saídas:**

```text
data/gold/product_metrics
data/gold/category_metrics
data/gold/user_metrics
data/gold/funnel_metrics
data/gold/user_product_interactions
```

**Score de produto:** `views * 1 + carts * 3 + purchases * 6 - removes * 2`.

**Score de interação:** `view = 1`, `cart = 3`, `purchase = 5`, `remove_from_cart = -1`.

## SPEC-05 — Recomendador Baseline

**Objetivo:** criar recomendador interpretável por popularidade ponderada e contexto de categoria.

**Arquivo:** `src/recommender_baseline.py`.

**Saídas:** `data/gold/recommendations_baseline` e `outputs/recommendations/baseline_top_products.parquet`.

**Requisitos:** Top N geral, por categoria, por marca e personalizado por usuário. Remover produtos já comprados pelo usuário.

## SPEC-06 — Avaliação do Baseline

**Objetivo:** avaliar com divisão temporal.

**Arquivo:** `src/evaluation.py`.

**Estratégia:** treino em meses anteriores e teste no mês mais recente.

**Métricas:** `Precision@K`, `Recall@K`, `Coverage`, usuários avaliados, recomendações totais e acertos.

**Saída:** `outputs/metrics/baseline_evaluation.json`.

## SPEC-07 — ALS com Spark MLlib

**Objetivo:** criar recomendador com feedback implícito.

**Arquivo:** `src/recommender_als.py`.

**Entrada:** `data/gold/user_product_interactions`.

**Saídas:** `data/gold/recommendations_als` e `outputs/recommendations/als_recommendations.parquet`.

**Configuração inicial:** `implicitPrefs=True`, `rank=20`, `maxIter=10`, `regParam=0.1`, `coldStartStrategy="drop"`.

## SPEC-08 — Avaliação do ALS

**Objetivo:** avaliar ALS com a mesma lógica do baseline.

**Arquivo:** `src/evaluation.py`.

**Saída:** `outputs/metrics/als_evaluation.json`.

**Aceite:** comparação direta entre baseline e ALS sem duplicação desnecessária de lógica.

## SPEC-09 — Benchmark CSV vs Parquet

**Arquivo:** `experiments/benchmark_csv_vs_parquet.py`.

**Consulta sugerida:** contar eventos por `event_type` e `event_month`.

**Métricas:** formato, linhas, tempo de leitura, tempo de agregação, tempo total e tamanho em disco.

**Saída:** `outputs/metrics/benchmark_csv_vs_parquet.json`.

## SPEC-10 — Benchmark de Particionamento

**Arquivo:** `experiments/benchmark_partitioning.py`.

**Estratégias:** sem particionamento, por `event_month`, por `event_type`, por ambos.

**Métricas:** tempo de escrita, leitura, consulta, quantidade de arquivos e tamanho em disco.

**Saída:** `outputs/metrics/benchmark_partitioning.json`.

## SPEC-11 — Benchmark de Escalabilidade

**Arquivo:** `experiments/benchmark_scalability.py`.

**Cenários:** 1 mês, 3 meses e todos os meses disponíveis.

**Métricas:** linhas processadas, tempo total e tempo por milhão de linhas.

**Saída:** `outputs/metrics/benchmark_scalability.json`.

## SPEC-12 — Benchmark de Cache

**Arquivo:** `experiments/benchmark_cache.py`.

**Experimento:** mesma agregação sem cache, com cache e segunda execução com cache.

**Métricas:** tempos, ganho percentual e linhas processadas.

**Saída:** `outputs/metrics/benchmark_cache.json`.

## SPEC-13 — API FastAPI

**Arquivo:** `src/api.py`.

**Endpoints:** `/health`, `/recommendations/user/{user_id}`, `/products/top`, `/products/category/{category_code}`, `/metrics/funnel`, `/metrics/performance`.

**Aceite:** API lê dados persistidos em Gold/outputs e não recalcula a pipeline por request.

## SPEC-14 — Dashboard Streamlit

**Arquivo:** `src/app.py`.

**Telas:** visão geral, funil, produtos mais comprados, categorias com maior receita, recomendações por usuário e benchmarks.

**Aceite:** dashboard consulta artefatos finais, não o dataset bruto.

## SPEC-15 — Figuras para o Artigo

**Arquivo:** `src/generate_figures.py`.

**Saídas:** `funnel.png`, `csv_vs_parquet.png`, `partitioning_benchmark.png`, `scalability.png`, `model_comparison.png`.

**Aceite:** gráficos em PNG com título, eixos e legenda quando necessário.

## SPEC-16 — Testes Automatizados

**Objetivo:** validar funções críticas com dados pequenos.

**Cobertura mínima:** SparkSession, schema de ingestão, limpeza, colunas temporais, métricas Gold, `weighted_score`, `Precision@K` e `Recall@K`.

**Comando:** `make test` ou `pytest`.

## SPEC-17 — Logging e Tempo

**Arquivo:** `src/utils.py`.

**Funções sugeridas:** `get_logger`, `measure_time`, `save_json`, `get_directory_size_mb`, `count_files`.

**Aceite:** scripts usam logs e métricas padronizadas.

## SPEC-18 — Makefile Final

**Comandos obrigatórios:**

```bash
make install
make test
make ingest
make preprocess
make features
make train-baseline
make evaluate-baseline
make train-als
make evaluate-als
make benchmark-csv-parquet
make benchmark-partitioning
make benchmark-scalability
make benchmark-cache
make benchmark
make figures
make api
make app
make clean
```

`make clean` não deve apagar `data/raw`.

## SPEC-19 — README Final

**Seções obrigatórias:** título, problema, dataset, arquitetura, estrutura, instalação, execução, benchmarks, API/dashboard, resultados esperados, limitações e próximos passos.

**Aceite:** um avaliador consegue reproduzir o projeto seguindo apenas o README.

## SPEC-20 — Execução Completa

**Comando esperado:** `make all` ou a sequência completa de ingestão, limpeza, features, modelos, avaliações, benchmarks e figuras.

**Saídas finais:** camadas Bronze, Silver e Gold, recomendações, métricas JSON e figuras para o artigo.

## Ordem Recomendada

```text
SPEC-00 -> SPEC-01 -> SPEC-17 -> SPEC-02 -> SPEC-03 -> SPEC-04
SPEC-05 -> SPEC-06 -> SPEC-09 -> SPEC-10 -> SPEC-11 -> SPEC-12
SPEC-07 -> SPEC-08 -> SPEC-15 -> SPEC-13 -> SPEC-14 -> SPEC-16
SPEC-18 -> SPEC-19 -> SPEC-20
```

Comece com uma amostra ou um mês do dataset. Depois expanda para múltiplos meses e, por fim, rode os experimentos completos.
