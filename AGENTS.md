# Instruções para o Codex — RetailRank

## Objetivo do Repositório

Implementar o **RetailRank**, uma pipeline Big Data com Apache Spark para processar eventos reais de e-commerce e gerar recomendações de produtos. O projeto deve sustentar um artigo acadêmico com evidências de desempenho, escalabilidade, particionamento e qualidade das recomendações.

## Prioridade de Trabalho

Siga a ordem definida em `SPECS.md`. A prioridade é ter uma pipeline funcional antes de adicionar interface visual:

1. Setup, configuração centralizada, SparkSession e utilitários.
2. Ingestão Raw -> Bronze em Parquet.
3. Limpeza Bronze -> Silver com schema consistente e particionamento.
4. Camada Gold com métricas e interações usuário-produto.
5. Recomendador baseline e avaliação.
6. Benchmarks de CSV vs Parquet, particionamento, escalabilidade e cache.
7. ALS, figuras, API, dashboard, testes finais e README.

## Estrutura Esperada

- `data/raw/`: CSVs originais do Kaggle. Não modificar nem apagar.
- `data/bronze/`: dados brutos convertidos para Parquet.
- `data/silver/`: dados limpos, tipados e particionados.
- `data/gold/`: métricas, features e recomendações.
- `src/`: código principal da pipeline, modelos, avaliação, API e dashboard.
- `experiments/`: benchmarks reprodutíveis.
- `outputs/metrics/`: métricas JSON de execução, avaliação e desempenho.
- `outputs/recommendations/`: saídas finais de recomendação.
- `outputs/figures/`: gráficos para o artigo.
- `tests/`: testes com dados pequenos em memória.

## Regras de Implementação

Use Spark como ferramenta principal de processamento. Não use Pandas para processar o dataset completo; Pandas só é aceitável para visualização, gráficos ou arquivos finais pequenos.

Centralize configurações em `src/config.py` e a criação da SparkSession em `src/spark_session.py`. Scripts não devem criar SparkSession manualmente. Evite paths absolutos locais; use constantes ou argumentos.

Cada etapa deve registrar tempo de execução, quantidade de linhas processadas quando aplicável e salvar métricas em JSON. Mantenha funções testáveis e separe leitura, transformação, escrita e cálculo de métricas.

## Comandos Esperados

O `Makefile` deve centralizar os comandos:

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
make benchmark
make figures
make api
make app
make clean
```

`make clean` pode remover dados derivados, mas nunca deve apagar `data/raw/`.

## Testes

Use `pytest`. Testes devem usar DataFrames pequenos, sintéticos e em memória. Não dependa dos CSVs grandes em `data/raw/`. Cubra SparkSession, schemas, filtros de limpeza, métricas Gold, score ponderado e métricas de avaliação.

## Critérios de Qualidade

Priorize clareza, reprodutibilidade, logs, métricas, particionamento e uso correto do Spark. Evite código monolítico, dependências desnecessárias, ausência de testes, ausência de métricas e interface visual antes da pipeline estar pronta.
