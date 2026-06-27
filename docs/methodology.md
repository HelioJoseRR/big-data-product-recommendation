# Metodologia

## Ambiente

O experimento roda localmente com Python 3.11+, Java 17 e Spark em modo `local[*]`. As dependencias Python estao em `requirements.txt`.

## Dataset

O dataset usado e o RetailRocket eCommerce Dataset. Os arquivos esperados sao `events.csv`, `item_properties_part1.csv`, `item_properties_part2.csv` e `category_tree.csv`, em `data/` ou `data/raw/`.

## Pipeline

A pipeline verifica os CSVs, le eventos com schema explicito, remove registros invalidos, converte timestamps e cria pesos implicitos: `view=1`, `addtocart=3`, `transaction=5`. Em seguida, agrega interacoes por usuario-item e salva dados processados em Parquet.

## Modelos

Sao avaliados tres modelos: popularidade global, coocorrencia item-item e ALS com feedback implicito.

## Metricas

A avaliacao usa Precision@10, Recall@10, MAP@10, NDCG@10 e Coverage. Apenas usuarios presentes no treino e no teste entram na avaliacao.

## Benchmarks

Os experimentos comparam modelos, fracoes do dataset, particionamento e leitura CSV vs Parquet.

## Reproducao

```bash
pip install -r requirements.txt
make check-data
make benchmark-smoke
make plot
make report
```
