"""Read JSONL data and enforce the declared provenance and split contract."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

VARIANTS = {"devanagari", "romanized", "code_switched", "control"}
ORIGINS = {"synthetic_fixture", "human_authored"}
REVIEW_STATUSES = {"unreviewed", "approved"}


class DataError(ValueError):
    """An input file violates the evaluation data contract."""


@dataclass(frozen=True)
class Dataset:
    documents: tuple[dict[str, Any], ...]
    queries: tuple[dict[str, Any], ...]
    source_sha256: dict[str, str]
    mode: str


def _string(value: Any, field: str, location: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DataError(f"{location}: {field} must be a nonempty string")


def _identifier(value: Any, field: str, location: str) -> None:
    _string(value, field, location)
    if value != value.strip():
        raise DataError(f"{location}: {field} must not have surrounding whitespace")


def _read_jsonl(path: Path) -> tuple[list[tuple[int, dict[str, Any]]], str]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise DataError(f"Cannot read {path.name} as UTF-8: {exc}") from exc
    rows = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DataError(
                f"{path.name}:{line_number}: malformed JSON: {exc.msg}"
            ) from exc
        if not isinstance(row, dict):
            raise DataError(f"{path.name}:{line_number}: each row must be an object")
        rows.append((line_number, row))
    if not rows:
        raise DataError(f"{path.name}: at least one record is required")
    return rows, hashlib.sha256(raw).hexdigest()


def has_declared_review(row: dict[str, Any]) -> bool:
    """Check metadata only; this is not independent verification of reviewers."""
    provenance = row["provenance"]
    reviewers = provenance["reviewer_ids"]
    return (
        provenance["origin"] == "human_authored"
        and provenance["review_status"] == "approved"
        and len(set(reviewers)) >= 2
        and provenance["author_id"] not in reviewers
    )


def _common(row: dict[str, Any], location: str, mode: str) -> None:
    _string(row.get("text"), "text", location)
    # Presence is checkable here; permission and license compatibility are not.
    _string(row.get("license"), "license", location)
    provenance = row.get("provenance")
    if not isinstance(provenance, dict):
        raise DataError(f"{location}: provenance must be an object")
    if not isinstance(provenance.get("origin"), str) or provenance["origin"] not in ORIGINS:
        raise DataError(f"{location}: provenance.origin must be synthetic_fixture or human_authored")
    if not isinstance(provenance.get("review_status"), str) or provenance["review_status"] not in REVIEW_STATUSES:
        raise DataError(f"{location}: provenance.review_status must be unreviewed or approved")
    _identifier(provenance.get("author_id"), "provenance.author_id", location)
    reviewers = provenance.get("reviewer_ids")
    if not isinstance(reviewers, list):
        raise DataError(f"{location}: provenance.reviewer_ids must be a list")
    for reviewer in reviewers:
        _identifier(reviewer, "reviewer ID", location)
    if len(reviewers) != len(set(reviewers)):
        raise DataError(f"{location}: reviewer_ids must be distinct")
    if provenance["author_id"] in reviewers:
        raise DataError(f"{location}: an author cannot be an independent reviewer")
    if mode == "benchmark":
        if provenance["origin"] != "human_authored":
            raise DataError(f"{location}: benchmark mode rejects synthetic fixtures")
        if provenance["review_status"] != "approved":
            raise DataError(f"{location}: benchmark mode requires approved human review")
        if len(reviewers) < 2:
            raise DataError(f"{location}: benchmark mode requires at least two distinct non-author reviewers")


def load_dataset(data_dir: str | Path, mode: str) -> Dataset:
    if mode not in {"smoke", "benchmark"}:
        raise DataError("mode must be smoke or benchmark")
    data_dir = Path(data_dir)
    doc_rows, doc_hash = _read_jsonl(data_dir / "docs.jsonl")
    query_rows, query_hash = _read_jsonl(data_dir / "queries.jsonl")

    documents = []
    doc_ids = set()
    for line, row in doc_rows:
        location = f"docs.jsonl:{line}"
        _common(row, location, mode)
        _identifier(row.get("doc_id"), "doc_id", location)
        _identifier(row.get("entity_id"), "entity_id", location)
        if row["doc_id"] in doc_ids:
            raise DataError(f"{location}: duplicate doc_id {row['doc_id']!r}")
        doc_ids.add(row["doc_id"])
        documents.append(row)

    queries = []
    query_ids = set()
    group_splits: dict[str, str] = {}
    for line, row in query_rows:
        location = f"queries.jsonl:{line}"
        _common(row, location, mode)
        for field in ("query_id", "group_id"):
            _identifier(row.get(field), field, location)
        if row["query_id"] in query_ids:
            raise DataError(f"{location}: duplicate query_id {row['query_id']!r}")
        query_ids.add(row["query_id"])
        if not isinstance(row.get("variant"), str) or row["variant"] not in VARIANTS:
            raise DataError(f"{location}: variant must be one of {', '.join(sorted(VARIANTS))}")
        if not isinstance(row.get("split"), str) or row["split"] not in {"dev", "test"}:
            raise DataError(f"{location}: split must be dev or test")
        prior_split = group_splits.setdefault(row["group_id"], row["split"])
        if prior_split != row["split"]:
            raise DataError(
                f"{location}: semantic group {row['group_id']!r} leaks across dev/test"
            )
        relevant = row.get("relevant_doc_ids")
        if not isinstance(relevant, list):
            raise DataError(f"{location}: relevant_doc_ids must be a list (empty means unanswerable)")
        for doc_id in relevant:
            _identifier(doc_id, "relevant document ID", location)
        if len(relevant) != len(set(relevant)):
            raise DataError(f"{location}: relevant_doc_ids must be distinct")
        missing = sorted(set(relevant) - doc_ids)
        if missing:
            raise DataError(f"{location}: relevant_doc_ids reference missing documents: {missing}")
        queries.append(row)

    return Dataset(
        tuple(documents), tuple(queries),
        {"docs.jsonl": doc_hash, "queries.jsonl": query_hash}, mode,
    )


def dataset_summary(dataset: Dataset) -> dict[str, Any]:
    return {
        "document_count": len(dataset.documents),
        "query_count": len(dataset.queries),
        "semantic_group_count": len({q["group_id"] for q in dataset.queries}),
        "source_sha256": dataset.source_sha256,
        "declared_reviewed_counts": {
            "documents": sum(has_declared_review(d) for d in dataset.documents),
            "queries": sum(has_declared_review(q) for q in dataset.queries),
        },
        "review_verification": "Input declarations only; reviewer identity and work are not independently verified.",
        "license_verification": "Input declarations only; maintainers must verify permissions and license compatibility.",
    }
