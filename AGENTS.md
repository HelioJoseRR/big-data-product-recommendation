# Repository Guidelines

## Objetivo

Este repositório implementa uma pipeline local com PySpark para benchmark de recomendação de produtos usando o dataset RetailRocket. O foco é gerar evidências para um artigo acadêmico: métricas de qualidade, tempo de execução, comparação de modelos, particionamento e armazenamento.

## Regras

- Priorize simplicidade, reprodutibilidade e execução local.
- Não implemente API web, frontend, Kafka, Airflow, MLflow ou serviços externos.
- Não versionar arquivos CSV, Parquet ou resultados gerados.
- Toda funcionalidade principal deve ser acessível pela CLI.
- Use Spark nas etapas principais de ingestão, limpeza, agregação e treino.
- Use Pandas apenas para ler CSVs pequenos de métricas e gerar gráficos.
- Use type hints quando razoável e `pathlib` para caminhos.
- Escreva testes para funções puras e smoke tests com dados pequenos.

## Estrutura

- `src/retailrocket_recsys/`: código da aplicação.
- `configs/default.yaml`: configuração padrão.
- `data/`: CSVs brutos e dados intermediários/processados.
- `results/metrics/`: CSVs de métricas.
- `results/figures/`: gráficos PNG.
- `results/reports/`: relatórios Markdown gerados.
- `docs/`: material de apoio para o artigo.
- `tests/`: testes automatizados.

## Critérios de Aceite

Antes de finalizar mudanças relevantes, execute:

```bash
make lint
make test
```

Se o dataset estiver disponível, execute também:

```bash
make benchmark-smoke
```

## Saídas Esperadas

- `results/metrics/*.csv`
- `results/figures/*.png`
- `results/reports/experiment_summary.md`
- `docs/methodology.md`
- `docs/experiment_plan.md`
