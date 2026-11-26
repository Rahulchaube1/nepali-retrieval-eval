"""Metrics with explicit denominators, provenance and software-demo status."""

from __future__ import annotations

import time
from typing import Any, Iterable

from . import __version__
from .data import Dataset, dataset_summary
from .retrieval import TfidfRetriever


def measure(
    queries: Iterable[dict[str, Any]],
    rankings: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    counts = {
        "queries": 0, "answerable": 0, "unanswerable": 0,
        "accepted": 0, "abstained": 0, "answerable_top1_correct": 0,
        "unanswerable_false_accepts": 0,
    }
    recalls, reciprocals = [], []
    for query in queries:
        counts["queries"] += 1
        candidates = rankings[query["query_id"]]
        ids = [candidate["doc_id"] for candidate in candidates]
        counts["accepted" if ids else "abstained"] += 1
        relevant = set(query["relevant_doc_ids"])
        if relevant:
            counts["answerable"] += 1
            counts["answerable_top1_correct"] += int(bool(ids) and ids[0] in relevant)
            recalls.append(len(set(ids[:5]) & relevant) / len(relevant))
            reciprocals.append(next(
                (1 / rank for rank, doc_id in enumerate(ids[:10], 1) if doc_id in relevant),
                0.0,
            ))
        else:
            counts["unanswerable"] += 1
            counts["unanswerable_false_accepts"] += int(bool(ids))
    answerable, unanswerable = counts["answerable"], counts["unanswerable"]
    return {
        "counts": counts,
        "answerable_top1_accuracy": counts["answerable_top1_correct"] / answerable if answerable else None,
        "answerable_recall_at_5": sum(recalls) / answerable if answerable else None,
        "answerable_mrr_at_10": sum(reciprocals) / answerable if answerable else None,
        "unanswerable_false_accept_rate": counts["unanswerable_false_accepts"] / unanswerable if unanswerable else None,
    }


def report_header(dataset: Dataset) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "tool": {"name": "nepali-retrieval-eval", "version": __version__},
        "mode": dataset.mode,
        "status": "software_demo_only" if dataset.mode == "smoke" else "human_review_declared",
        "interpretation": (
            "Smoke metrics exercise software only. They make no Nepali or language-performance claim."
            if dataset.mode == "smoke"
            else "Metrics describe the supplied dataset with declared human authorship and review; metadata is not independent verification."
        ),
        "data": dataset_summary(dataset),
    }


def run_baseline(dataset: Dataset, baseline: str) -> dict[str, Any]:
    started = time.perf_counter()
    retriever = TfidfRetriever(dataset.documents, baseline)
    rankings = {
        query["query_id"]: retriever.rank(query["text"])
        for query in sorted(dataset.queries, key=lambda query: query["query_id"])
    }
    report = report_header(dataset)
    report.update({
        "baseline": retriever.description(),
        "metrics": measure(dataset.queries, rankings),
        "breakdown_by_variant": {
            variant: measure((q for q in dataset.queries if q["variant"] == variant), rankings)
            for variant in sorted({q["variant"] for q in dataset.queries})
        },
        "breakdown_by_split": {
            split: measure((q for q in dataset.queries if q["split"] == split), rankings)
            for split in sorted({q["split"] for q in dataset.queries})
        },
        "metric_definitions": {
            "answerable_top1_accuracy": "Correct first results / all answerable queries; abstentions count as incorrect.",
            "answerable_recall_at_5": "Macro average of relevant documents retrieved in top five / relevant documents for each answerable query.",
            "answerable_mrr_at_10": "Macro reciprocal rank of first relevant result within ten; absent results score zero.",
            "unanswerable_false_accept_rate": "Unanswerable queries with a positive-score result / all unanswerable queries.",
            "missing_denominator": "A metric is null when its denominator is zero.",
        },
        "rankings": [
            {
                "query_id": query["query_id"],
                "group_id": query["group_id"],
                "variant": query["variant"],
                "split": query["split"],
                "answerable": bool(query["relevant_doc_ids"]),
                "accepted_doc_id": rankings[query["query_id"]][0]["doc_id"] if rankings[query["query_id"]] else None,
                "candidates": rankings[query["query_id"]],
            }
            for query in sorted(dataset.queries, key=lambda query: query["query_id"])
        ],
        "elapsed_seconds": time.perf_counter() - started,
        "timing_scope": "Baseline indexing, retrieval and report construction; excludes file loading and validation.",
    })
    return report
