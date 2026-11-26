# Evaluation protocol

Nepali Script Retrieval Evaluation · v0.1.0 · 26 November 2026

## Status and research question

This is an independent evaluation starter. Human data collection is pending: **zero human-validated records are included**. The synthetic fixtures contain mechanical control strings, not translation candidates. Any fixture scores verify software behavior; they do not measure Nepali retrieval quality.

The proposed question is whether a retrieval system finds the same relevant documents when a native speaker expresses a query in Devanagari Nepali, romanized Nepali, or Nepali–English code-switching. Matched meaning is a human judgment to establish, not an assumption justified by script conversion.

## Human authoring and review

1. Recruit consenting native Nepali speakers with sufficient English proficiency for the mixed-language task. Record the language variety, intended register, and authorship process. Obtain permission for the intended public release and record the agreed license. Use public pseudonym IDs; keep contact information and consent records separately with appropriate access restrictions.
2. Ask authors to write fresh source passages, relevant documents, and plausible entity distractors. Prefer fictional situations and entities. Avoid scraped news, private correspondence, sensitive personal data, and facts whose truth changes over time. Do not import protected benchmark text or derivatives.
3. Create a semantic group containing independently human-written queries in all three variants. Preserve information need, entities, negation, time constraints, and ambiguity. Natural romanization and code-switching can have multiple acceptable forms; record accepted alternatives rather than enforcing one spelling convention. Do not generate translation candidates with an AI system and call their subsequent approval independent human authorship.
4. Assign each document and query to two distinct reviewers, neither its author. Reviewers initially work independently. They check meaning, naturalness, register, answerability, entity identity, and relevance labels. Record their decisions before reconciliation. An adjudicator resolves disagreements; retain the disagreement history and rationale. Only complete, approved records enter benchmark mode.

Do not make the answer recoverable from filenames, IDs, repeated templates, or conspicuous entity-name overlap alone. Include plausible distractors and inspect lexical shortcuts. Do not claim factual reliability outside these deliberately bounded passages.

## Splits and provenance

Assign every variant and accepted alternative in a semantic group to the same `dev` or `test` split. Tune prompts, retrieval settings, acceptance thresholds, and normalization on development material only. Freeze test queries and relevance labels before comparisons; check for near-duplicates, reused templates, and overlapping semantic groups across splits.

Use the JSONL schemas described in the project README. Each document and query records origin, author ID, reviewer IDs, review status, and license. `entity_id` identifies a document's intended entity. A query with an empty `relevant_doc_ids` list is deliberately unanswerable within the corpus, not an unlabeled example. The CSV templates support collection; their rows require conversion into the documented JSONL schema.

The benchmark gate requires declared `human_authored` origin, `approved` status, and two distinct reviewer IDs different from the author for documents and queries. **These checks validate metadata, not the existence, independence, consent, or competence of human participants.** The dataset maintainer must verify those facts against the private review record.

## Measures and reporting

Report results by query variant and split, with denominators. For answerable queries, macro-average:

- **Recall@5:** relevant documents among the first five results divided by all labeled relevant documents.
- **MRR@10:** reciprocal rank of the first relevant document within ten results; zero if absent.
- **Top-1 accuracy:** proportion whose first returned document is relevant.

For unanswerable queries, report **false-accept rate:** the fraction for which the system accepts a retrieved answer under a declared acceptance rule. Fix any score threshold on development data. Also report acceptance coverage so a system cannot appear reliable simply by rejecting everything. A missing denominator is unavailable, not zero performance.

Record corpus/query versions and hashes, model and tokenizer revisions, dependencies, hardware, normalization, prompts, indexing settings, score thresholds, tie handling, and random seeds. Preserve per-query outputs locally; publish only outputs permitted by the data's terms. Explain exclusions and accepted variants.

For future confidence intervals, resample semantic groups rather than treating their correlated variants as independent observations. Group-level bootstrap is recommended but **not implemented in v0.1.0**. This release makes no statistical-power or sample-size sufficiency claim. Human evaluation results remain pending.
