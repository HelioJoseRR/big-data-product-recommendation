# RetailRank — Visão do Projeto

## Visão Geral

O RetailRank é uma aplicação Big Data para recomendação de produtos em e-commerce. O projeto usa Apache Spark para processar eventos reais de navegação, carrinho e compra, gerando métricas analíticas, recomendações e evidências de desempenho para um artigo acadêmico.

Dataset de referência:

```text
https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store/data
```

Os CSVs brutos devem ficar em:

```text
./data/raw
```

## Problema

Lojas virtuais geram grandes volumes de eventos, como visualizações, adições ao carrinho, remoções e compras. O desafio é processar esses dados em larga escala para identificar produtos relevantes, categorias com melhor conversão, intenção de compra dos usuários e impactos de formato, volume e particionamento no desempenho.

## Objetivos

- Ler arquivos CSV em `data/raw`.
- Converter dados para Parquet.
- Criar camadas Bronze, Silver e Gold.
- Gerar métricas de usuários, produtos, categorias e funil.
- Implementar recomendador baseline por popularidade ponderada.
- Implementar ALS com Spark MLlib, se viável.
- Avaliar recomendações com `Precision@K`, `Recall@K` e `Coverage`.
- Comparar CSV vs Parquet, estratégias de particionamento, cache e escalabilidade.
- Produzir API ou dashboard simples para consulta de resultados.

## Dataset

Campos esperados:

```text
event_time
event_type
product_id
category_id
category_code
brand
price
user_id
user_session
```

Eventos esperados:

```text
view
cart
remove_from_cart
purchase
```

## Arquitetura em Camadas

```text
data/raw
  -> data/bronze
  -> data/silver
  -> data/gold
  -> modelos de recomendação
  -> outputs finais
  -> API ou dashboard
```

### Raw

Entrada original do Kaggle. Não deve ser modificada.

### Bronze

Dados lidos do CSV com schema explícito e salvos em Parquet com transformações mínimas.

### Silver

Dados limpos, tipados, filtrados e particionados por `event_month` e `event_type`.

### Gold

Agregações e features para análise, recomendação e avaliação:

```text
product_metrics
category_metrics
user_metrics
funnel_metrics
user_product_interactions
recommendations_baseline
recommendations_als
```

## Métricas Principais

Produtos: visualizações, carrinhos, remoções, compras, receita estimada, taxa de conversão, taxa de carrinho e score ponderado.

Categorias: eventos totais, compras, receita estimada e conversão.

Usuários: eventos totais, produtos vistos, produtos comprados e gasto total.

Funil: distribuição percentual por tipo de evento.

## Recomendação

O baseline deve usar score ponderado:

```text
views * 1 + carts * 3 + purchases * 6 - removes * 2
```

O ALS deve usar feedback implícito com interações:

```text
view = 1
cart = 3
purchase = 5
remove_from_cart = -1
```

## Resultado Esperado

Ao final, o projeto deve responder:

- Quais produtos recomendar para um usuário?
- Quais produtos têm maior potencial de compra?
- Quais categorias convertem melhor?
- Qual foi o ganho de desempenho usando Parquet?
- Qual particionamento foi mais eficiente?
- Como o tempo cresce com o volume de dados?
