"""Provenance gates and hand-computed metric cases, using artificial controls."""

from __future__ import annotations

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

from nepali_eval.cli import main
from nepali_eval.data import DataError, load_dataset
from nepali_eval.evaluation import measure, run_baseline
from nepali_eval.retrieval import TfidfRetriever, normalize_text, word_features


def provenance(human=False):
    return {
        "origin": "human_authored" if human else "synthetic_fixture",
        "author_id": "author-a",
        "reviewer_ids": ["reviewer-a", "reviewer-b"] if human else [],
        "review_status": "approved" if human else "unreviewed",
    }


def fixtures(human=False):
    docs = [
        {"doc_id": "a", "text": "amber widget", "entity_id": "entity-a", "provenance": provenance(human), "license": "CC0-1.0"},
        {"doc_id": "b", "text": "azure gadget", "entity_id": "entity-b", "provenance": provenance(human), "license": "CC0-1.0"},
    ]
    queries = [
        {"query_id": "q1", "group_id": "g1", "text": "amber widget", "variant": "control", "split": "dev", "relevant_doc_ids": ["a"], "provenance": provenance(human), "license": "CC0-1.0"},
        {"query_id": "q2", "group_id": "g2", "text": "%%%%%%", "variant": "control", "split": "test", "relevant_doc_ids": [], "provenance": provenance(human), "license": "CC0-1.0"},
    ]
    return docs, queries


class DataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, docs, queries):
        for filename, rows in (("docs.jsonl", docs), ("queries.jsonl", queries)):
            (self.path / filename).write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )

    def test_synthetic_smoke_is_labeled_and_benchmark_rejects_it(self):
        self.write(*fixtures())
        data = load_dataset(self.path, "smoke")
        for baseline in ("word_tfidf", "char_tfidf"):
            report = run_baseline(data, baseline)
            self.assertEqual(report["status"], "software_demo_only")
            self.assertEqual(report["data"]["declared_reviewed_counts"], {"documents": 0, "queries": 0})
            self.assertEqual(report["metrics"]["answerable_top1_accuracy"], 1.0)
            self.assertEqual(report["metrics"]["unanswerable_false_accept_rate"], 0.0)
            self.assertEqual(len(report["data"]["source_sha256"]["docs.jsonl"]), 64)
        with self.assertRaisesRegex(DataError, "rejects synthetic"):
            load_dataset(self.path, "benchmark")

    def test_review_gate_applies_to_both_documents_and_queries(self):
        for collection in ("docs", "queries"):
            for issue in ("unreviewed", "one_reviewer", "author_reviewer", "duplicate_reviewer", "synthetic"):
                with self.subTest(collection=collection, issue=issue):
                    docs, queries = fixtures(human=True)
                    row = (docs if collection == "docs" else queries)[0]
                    p = row["provenance"]
                    if issue == "unreviewed":
                        p["review_status"] = "unreviewed"
                    elif issue == "one_reviewer":
                        p["reviewer_ids"] = ["reviewer-a"]
                    elif issue == "author_reviewer":
                        p["reviewer_ids"] = ["author-a", "reviewer-a"]
                    elif issue == "duplicate_reviewer":
                        p["reviewer_ids"] = ["reviewer-a", "reviewer-a"]
                    else:
                        p["origin"] = "synthetic_fixture"
                    self.write(docs, queries)
                    with self.assertRaises(DataError):
                        load_dataset(self.path, "benchmark")

    def test_complete_declared_human_review_can_pass(self):
        self.write(*fixtures(human=True))
        data = load_dataset(self.path, "benchmark")
        self.assertEqual(len(data.documents), 2)
        self.assertEqual(run_baseline(data, "word_tfidf")["status"], "human_review_declared")

    def test_licenses_are_declared_and_not_certified(self):
        docs, queries = fixtures(human=True)
        for row in docs + queries:
            row["license"] = "CC-BY-4.0"
        self.write(docs, queries)
        data = load_dataset(self.path, "benchmark")
        self.assertEqual(data.documents[0]["license"], "CC-BY-4.0")
        self.assertEqual(data.queries[0]["license"], "CC-BY-4.0")
        for collection in ("documents", "queries"):
            for blank in ("", "   "):
                with self.subTest(collection=collection, blank=blank):
                    changed_docs, changed_queries = copy.deepcopy(docs), copy.deepcopy(queries)
                    rows = changed_docs if collection == "documents" else changed_queries
                    rows[0]["license"] = blank
                    self.write(changed_docs, changed_queries)
                    with self.assertRaisesRegex(DataError, "license must be a nonempty string"):
                        load_dataset(self.path, "benchmark")

    def test_semantic_variants_cannot_cross_splits(self):
        docs, queries = fixtures()
        queries[1]["group_id"] = queries[0]["group_id"]
        self.write(docs, queries)
        with self.assertRaisesRegex(DataError, "leaks across dev/test"):
            load_dataset(self.path, "smoke")

    def test_duplicate_ids_and_missing_relevance_targets_fail(self):
        for issue in ("doc", "query", "missing"):
            with self.subTest(issue=issue):
                docs, queries = fixtures()
                if issue == "doc":
                    docs.append(copy.deepcopy(docs[0]))
                elif issue == "query":
                    queries.append(copy.deepcopy(queries[0]))
                else:
                    queries[0]["relevant_doc_ids"] = ["absent"]
                self.write(docs, queries)
                with self.assertRaisesRegex(DataError, "duplicate|missing documents"):
                    load_dataset(self.path, "smoke")

    def test_malformed_line_has_filename_and_line_number(self):
        self.write(*fixtures())
        with (self.path / "queries.jsonl").open("a", encoding="utf-8") as handle:
            handle.write("{broken}\n")
        with self.assertRaisesRegex(DataError, "queries.jsonl:3: malformed JSON"):
            load_dataset(self.path, "smoke")

    def test_malformed_types_and_ambiguous_reviewer_ids_fail_clearly(self):
        for issue in ("origin", "variant", "split", "reviewer"):
            with self.subTest(issue=issue):
                docs, queries = fixtures(human=True)
                if issue == "origin":
                    docs[0]["provenance"]["origin"] = []
                elif issue in {"variant", "split"}:
                    queries[0][issue] = []
                else:
                    docs[0]["provenance"]["reviewer_ids"] = ["reviewer-a", " reviewer-a"]
                self.write(docs, queries)
                with self.assertRaises(DataError):
                    load_dataset(self.path, "benchmark")

    def test_cli_reports_gate_error_without_creating_output(self):
        self.write(*fixtures())
        output = self.path / "result.json"
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            status = main(["run", "--data-dir", str(self.path), "--mode", "benchmark", "--baseline", "word_tfidf", "--output", str(output)])
        self.assertEqual(status, 2)
        self.assertFalse(output.exists())
        self.assertIn("benchmark mode rejects synthetic", error.getvalue())


class RankingAndMetricTests(unittest.TestCase):
    def test_metrics_match_hand_computed_multi_relevant_case(self):
        queries = [
            {"query_id": "a", "relevant_doc_ids": ["d1", "d2"]},
            {"query_id": "b", "relevant_doc_ids": ["d3"]},
            {"query_id": "c", "relevant_doc_ids": []},
            {"query_id": "d", "relevant_doc_ids": []},
        ]
        rankings = {
            "a": [{"doc_id": d, "score": 1.0} for d in ("d2", "d3", "d4", "d5", "d6", "d1")],
            "b": [{"doc_id": d, "score": 1.0} for d in ("d4", "d3")],
            "c": [{"doc_id": "d1", "score": 1.0}],
            "d": [],
        }
        metrics = measure(queries, rankings)
        self.assertEqual(metrics["answerable_top1_accuracy"], 0.5)
        self.assertEqual(metrics["answerable_recall_at_5"], 0.75)
        self.assertEqual(metrics["answerable_mrr_at_10"], 0.75)
        self.assertEqual(metrics["unanswerable_false_accept_rate"], 0.5)
        self.assertEqual(metrics["counts"]["accepted"], 3)
        self.assertEqual(metrics["counts"]["abstained"], 1)

    def test_absent_denominator_is_null_and_answerable_abstention_is_zero(self):
        metrics = measure([{"query_id": "a", "relevant_doc_ids": ["d1"]}], {"a": []})
        self.assertEqual(metrics["answerable_top1_accuracy"], 0.0)
        self.assertEqual(metrics["answerable_recall_at_5"], 0.0)
        self.assertEqual(metrics["answerable_mrr_at_10"], 0.0)
        self.assertIsNone(metrics["unanswerable_false_accept_rate"])

    def test_ties_are_deterministic_and_ignore_labels_and_input_order(self):
        docs = [
            {"doc_id": "z", "text": "shared control", "relevant_doc_ids": ["z"]},
            {"doc_id": "a", "text": "shared control", "relevant_doc_ids": []},
        ]
        for baseline in ("word_tfidf", "char_tfidf"):
            first = TfidfRetriever(docs, baseline).rank("shared control")
            reverse = TfidfRetriever(reversed(docs), baseline).rank("shared control")
            self.assertEqual(first, reverse)
            self.assertEqual([row["doc_id"] for row in first], ["a", "z"])

    def test_zero_overlap_abstains(self):
        for baseline in ("word_tfidf", "char_tfidf"):
            self.assertEqual(TfidfRetriever([{"doc_id": "a", "text": "amber widget"}], baseline).rank("%%%%%%"), [])

    def test_nfc_and_combining_marks_are_preserved(self):
        self.assertEqual(normalize_text("CAFE\u0301"), "café")
        self.assertEqual(word_features("a\u0331b"), ["a\u0331b"])
        retriever = TfidfRetriever([{"doc_id": "a", "text": "café"}], "word_tfidf")
        self.assertEqual(retriever.rank("cafe\u0301")[0]["doc_id"], "a")


if __name__ == "__main__":
    unittest.main()
