# Reproducao online gratuita com medicoes de cluster

Este guia descreve uma reproducao online e gratuita usando GitHub Codespaces
com um cluster Spark standalone em Docker Compose. O cluster roda em containers
separados dentro do Codespace:

- `spark-master`: Spark Master e UI na porta `8080`.
- `spark-worker-1`: worker com UI na porta `8081`.
- `spark-worker-2`: worker com UI na porta `8082`.
- `spark-history`: Spark History Server na porta `18080`.
- `app`: container que executa a CLI do projeto e expõe a Spark Application UI na porta `4040`.

Observacao: a cota gratuita do Codespaces e limitada. Rode primeiro o smoke
benchmark; execute o full benchmark apenas se houver tempo de cota suficiente.

## 1. Publicar ou abrir o repositorio no GitHub

O caminho mais simples e publicar este repositorio no GitHub e abrir:

```text
Code -> Codespaces -> Create codespace on main
```

Tambem e possivel criar um Codespace vazio e clonar o repositorio manualmente.

## 2. Construir a imagem do projeto

No terminal do Codespace:

```bash
docker compose -f docker-compose.cluster.yml build
```

## 3. Baixar o dataset para `data/raw`

O dataset deve ficar dentro do workspace, nao apenas no cache do Kaggle, para
que master, workers e app vejam os mesmos arquivos pelo volume `/app`.

```bash
docker compose -f docker-compose.cluster.yml run --rm app \
  bash -lc "pip install kagglehub && python scripts/download_retailrocket_kagglehub.py"
```

Confira:

```bash
docker compose -f docker-compose.cluster.yml run --rm app make check-data
```

## 4. Subir o cluster Spark

```bash
mkdir -p data/interim/spark-events
docker compose -f docker-compose.cluster.yml up -d spark-master spark-worker-1 spark-worker-2 spark-history
```

Veja se os workers registraram no master:

```bash
docker compose -f docker-compose.cluster.yml logs --tail=80 spark-master
```

No Codespaces, abra a aba **Ports** e torne visiveis estas portas:

- `8080`: Spark Master UI.
- `8081`: Worker 1 UI.
- `8082`: Worker 2 UI.
- `18080`: Spark History Server.
- `4040`: Spark Application UI durante uma execucao ativa.

## 5. Rodar primeiro o benchmark smoke

```bash
docker compose -f docker-compose.cluster.yml run --rm --service-ports app \
  python -m retailrocket_recsys.cli benchmark \
  --config-path configs/codespaces-cluster.yaml \
  --fractions 0.25 \
  --partitions 4 \
  --models popularity,als \
  --smoke
```

Durante a execucao, acompanhe:

- `http://localhost:8080`: estado do cluster e workers.
- `http://localhost:4040`: jobs, stages, SQL, executors e storage da aplicacao ativa.
- `http://localhost:18080`: historico apos a aplicacao encerrar.

## 6. Rodar o benchmark completo

Use apenas se o smoke finalizou e a cota do Codespaces permitir.

```bash
docker compose -f docker-compose.cluster.yml run --rm --service-ports app \
  python -m retailrocket_recsys.cli benchmark \
  --config-path configs/codespaces-cluster.yaml
```

O benchmark completo avalia:

- fracoes `0.25`, `0.50`, `0.75` e `1.00`;
- particoes `2`, `4`, `8` e `16`;
- modelos `popularity`, `cooccurrence` e `als`;
- leitura CSV versus Parquet.

## 7. Gerar perfil, dados processados e relatorio

```bash
docker compose -f docker-compose.cluster.yml run --rm app \
  python -m retailrocket_recsys.cli profile \
  --config-path configs/codespaces-cluster.yaml

docker compose -f docker-compose.cluster.yml run --rm app \
  python -m retailrocket_recsys.cli prepare \
  --config-path configs/codespaces-cluster.yaml

docker compose -f docker-compose.cluster.yml run --rm app \
  python -m retailrocket_recsys.cli report \
  --config-path configs/codespaces-cluster.yaml
```

## 8. Coletar metricas do cluster

Registre no artigo:

- Quantidade de workers: `2`.
- Cores por worker: `2`.
- Memoria por worker: `3g`.
- Master URL: `spark://spark-master:7077`.
- `spark.sql.shuffle.partitions`: `16`.
- Tempo total da aplicacao.
- Tempo por job/stage.
- Numero de tasks.
- Shuffle read/write.
- Input size.
- Executor runtime.
- JVM GC time.
- Falhas ou reexecucoes de tasks, se houver.

As metricas ficam nas abas:

- Spark Application UI `4040`: `Jobs`, `Stages`, `SQL`, `Executors`.
- Spark History Server `18080`: execucoes encerradas.
- Spark Master UI `8080`: workers vivos, cores e memoria.

## 9. Salvar resultados

Os artefatos ficam no workspace do Codespace:

- `results/metrics/*.csv`
- `results/figures/*.png`
- `results/reports/*.md`
- `data/interim/spark-events/`

Baixe esses arquivos pelo painel do Codespaces ou compacte:

```bash
tar -czf online-results.tar.gz results data/interim/spark-events
```

## 10. Encerrar o cluster para poupar cota

```bash
docker compose -f docker-compose.cluster.yml down
```

Depois pare o Codespace no GitHub para nao consumir tempo gratuito.

## Limites desta reproducao gratuita

Esta abordagem mede um cluster Spark standalone real, com master e workers
separados em containers. Entretanto, todos os containers rodam dentro da mesma
maquina virtual do Codespace. Portanto, ela e adequada para reproducao online
gratuita e coleta de metricas Spark, mas nao substitui uma avaliacao em varias
maquinas fisicas ou em um cluster cloud pago.
