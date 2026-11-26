# Nepali Script Retrieval Evaluation

An independent, open protocol and software starter for studying retrieval across Nepali Devanagari, Romanized Nepali and Nepali-English code-switching.

**Status: v0.1.0 — evaluation tooling, not a validated language benchmark.** There are **zero human-validated evaluation records**. The included eight documents and twelve queries are artificial software fixtures, clearly marked as AI-authored and unreviewed. No model-quality result is claimed.

## Research question

Does a retriever preserve the intended entity and meaning when the same information need is expressed in different scripts or mixed language? How often does a spelling-tolerant system incorrectly merge distinct entities?

A future human-authored collection will pair variants of one information need with a fixed document collection, plausible distractors, accepted variants and explicit relevance judgments. The [protocol](docs/protocol.md) defines collection, independent review, split grouping and reporting before data collection begins.

## What is included

- A dependency-free Python validator, lexical baselines and retrieval scorer.
- Word TF-IDF and character TF-IDF cosine baselines for checking the pipeline. Neither is a semantic or cross-script model.
- Separate software-fixture and benchmark modes. Benchmark mode rejects synthetic/unapproved rows and requires declared independent review metadata. This validates metadata; it cannot certify that a person performed the review.
- Answerable-query top-1 accuracy, Recall@5 and MRR@10; false acceptance of unanswerable queries; counts and breakdowns by variant.
- Provenance fields, file hashes and recorded run metadata.
- [Human authoring](templates/human-authoring.csv) and [review-log](templates/review-log.csv) templates, a [data card](DATA_CARD.md), and [community contribution routes](docs/community-routes.md).

## Run locally

Python 3.10 or newer; no model downloads, API keys or third-party runtime packages are needed. From the repository root:

```bash
PYTHONPATH=src python -m nepali_eval validate --data-dir data/smoke --mode smoke
PYTHONPATH=src python -m nepali_eval run --data-dir data/smoke --mode smoke --baseline word_tfidf --output results/smoke-word.json
PYTHONPATH=src python -m nepali_eval run --data-dir data/smoke --mode smoke --baseline char_tfidf --output results/smoke-char.json
PYTHONPATH=src python -m unittest discover -s tests -v
```

The generated results are software demonstrations only. A useful guard check is:

```bash
PYTHONPATH=src python -m nepali_eval validate --data-dir data/smoke --mode benchmark
```

That command is expected to fail: synthetic fixtures are not benchmark data.

## Data format

A data directory contains `docs.jsonl` and `queries.jsonl`. Each document has a unique `doc_id`, `text`, `entity_id`, `license` and `provenance`. Each query has `query_id`, `group_id`, `text`, `variant`, `split`, `relevant_doc_ids`, `license` and `provenance`. An empty relevance list means the corpus contains no acceptable answer.

`provenance` records `origin`, `author_id`, `reviewer_ids` and `review_status`. Human benchmark data must use `human_authored`, `approved`, and at least two distinct reviewers other than the author for both documents and queries. All variants in a semantic group must remain in the same split. See the data card for the full expectations.

## Relationship to community benchmarks

[BOUQuET](https://huggingface.co/spaces/facebook/bouquet) and [FLORES+](https://huggingface.co/datasets/openlanguagedata/flores_plus) already include Nepali. They provide community routes for human translations, validation and corrections. This repository is independent and is not a submission to, extension accepted by, or endorsement from either project or Meta.

Official translations must follow the respective human-authorship requirements. Their access and redistribution conditions also apply independently of this repository's license. No official benchmark text, modified benchmark rows, private correspondence, access credentials or restricted exports are included here.

## Before the first research release

1. Agree on a collection scope with qualified Nepali-language contributors.
2. Collect fresh human-authored material and consent; have it independently reviewed and adjudicated.
3. Freeze semantic-group splits and the document collection.
4. Freeze baseline/model revisions, parameters and the development-only calibration procedure.
5. Run the locked evaluation and publish denominators, errors, uncertainty and limitations.

All five stages remain necessary; passing the software checks does not establish linguistic validity. Bootstrap uncertainty estimates and pretrained multilingual model comparisons are planned, not implemented or measured in this release.

## Maintainer, provenance and license

Maintained by [Rahul Chaube](https://github.com/Rahulchaube1). The initial code, documentation and artificial smoke fixtures were prepared with AI assistance. The repository does not claim native-human authorship of the fixtures or any peer-reviewed publication.

Code and documentation: [MIT](LICENSE). Original artificial fixtures: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Future community-authored data requires its own documented permission and license.
