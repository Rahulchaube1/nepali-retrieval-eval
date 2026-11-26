"""Small lexical baselines using sparse dictionaries and corpus-only IDF."""

from __future__ import annotations

import math
import unicodedata
from collections import Counter
from typing import Any, Iterable

BASELINES = ("word_tfidf", "char_tfidf")


def normalize_text(text: str) -> str:
    # NFC preserves canonical equivalence without compatibility folding scripts.
    return " ".join(unicodedata.normalize("NFC", text.casefold()).split())


def word_features(text: str) -> list[str]:
    # Include combining marks: Python's regex \w alone splits many Indic words.
    tokens, current = [], []
    for character in normalize_text(text):
        if unicodedata.category(character)[0] in {"L", "M", "N"}:
            current.append(character)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tokens


def char_features(text: str) -> list[str]:
    normalized = normalize_text(text)
    return [
        normalized[start:start + width]
        for width in (3, 4, 5)
        for start in range(len(normalized) - width + 1)
    ]


class TfidfRetriever:
    """No relevance labels are read during ranking; ties use document IDs only."""

    def __init__(self, documents: Iterable[dict[str, Any]], baseline: str):
        if baseline not in BASELINES:
            raise ValueError(f"Unknown baseline: {baseline}")
        self.baseline = baseline
        self.features = word_features if baseline == "word_tfidf" else char_features
        documents = sorted(documents, key=lambda document: document["doc_id"])
        counts = {
            document["doc_id"]: Counter(self.features(document["text"]))
            for document in documents
        }
        frequencies: Counter[str] = Counter()
        for document_counts in counts.values():
            frequencies.update(document_counts.keys())
        self.idf = {
            feature: math.log((1 + len(documents)) / (1 + frequency)) + 1
            for feature, frequency in frequencies.items()
        }
        self.vectors = {
            doc_id: self._vector(document_counts)
            for doc_id, document_counts in counts.items()
        }

    def _vector(self, counts: Counter[str]) -> dict[str, float]:
        weights = {
            feature: (1 + math.log(count)) * self.idf[feature]
            for feature, count in counts.items()
            if feature in self.idf
        }
        norm = math.sqrt(sum(weight * weight for weight in weights.values()))
        return {feature: weight / norm for feature, weight in weights.items()} if norm else {}

    def rank(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        query_vector = self._vector(Counter(self.features(query)))
        results = []
        for doc_id, document_vector in self.vectors.items():
            score = sum(
                weight * document_vector.get(feature, 0.0)
                for feature, weight in sorted(query_vector.items())
            )
            if score > 0.0:
                results.append({"doc_id": doc_id, "score": score})
        results.sort(key=lambda result: (-result["score"], result["doc_id"]))
        return results[:limit]

    def description(self) -> dict[str, Any]:
        return {
            "name": self.baseline,
            "version": "1",
            "features": "Unicode letters/marks/numbers" if self.baseline == "word_tfidf" else "character n-grams of lengths 3, 4 and 5",
            "normalization": "case-fold, Unicode NFC, collapse whitespace",
            "tf": "1 + ln(count)",
            "idf": "1 + ln((1 + document_count) / (1 + document_frequency))",
            "idf_fit": "documents only; query relevance labels are never used",
            "similarity": "cosine",
            "tie_break": "document ID ascending",
            "abstention": "no candidate with a strictly positive score",
        }
