from __future__ import annotations

import math


def precision_at_k(recommended: list[int], relevant: list[int], k: int) -> float:
    if k <= 0:
        return 0.0
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    hits = sum(1 for item in recommended[:k] if item in relevant_set)
    return hits / k


def recall_at_k(recommended: list[int], relevant: list[int], k: int) -> float:
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    hits = sum(1 for item in recommended[:k] if item in relevant_set)
    return hits / len(relevant_set)


def average_precision_at_k(recommended: list[int], relevant: list[int], k: int) -> float:
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    hits = 0
    precision_sum = 0.0
    for index, item in enumerate(recommended[:k], start=1):
        if item in relevant_set:
            hits += 1
            precision_sum += hits / index
    return precision_sum / min(len(relevant_set), k)


def ndcg_at_k(recommended: list[int], relevant: list[int], k: int) -> float:
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    dcg = 0.0
    for index, item in enumerate(recommended[:k], start=1):
        if item in relevant_set:
            dcg += 1.0 / math.log2(index + 1)
    ideal_hits = min(len(relevant_set), k)
    idcg = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
    return dcg / idcg if idcg else 0.0
