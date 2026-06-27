# Plano de Experimentos

## Experimento 1: Comparacao de Modelos

Comparar popularidade global, coocorrencia item-item e ALS. Medir tempo de treino, avaliacao, Precision@10, Recall@10, MAP@10 e Coverage.

## Experimento 2: Escalabilidade por Fracao do Dataset

Executar a pipeline com fracoes de 25%, 50%, 75% e 100%. A amostragem e deterministica por `visitorid` para manter reprodutibilidade.

## Experimento 3: Particionamento

Executar agregacoes com 2, 4, 8 e 16 particoes, reparticionando por `visitorid`. Comparar tempo total e metricas.

## Experimento 4: CSV vs Parquet

Comparar tempo de leitura e contagem entre CSV bruto e Parquet processado. Registrar tamanho em disco e numero de linhas.
