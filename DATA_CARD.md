# Data card

**Project:** Nepali Script Retrieval Evaluation  
**Version:** 0.1.0  
**Date:** 26 November 2026  
**Status:** Engineering starter; human data collection pending.

## Contents and purpose

This release includes synthetic mechanical control-string fixtures and empty human-authoring/review templates. **Human-validated records: 0.** Fixtures are neither natural Nepali nor generated translation candidates. Their scores test evaluation mechanics and cannot support language-quality, model-superiority, or population-level claims.

The intended future dataset will contain fresh human-authored source documents, entity distractors, and matched-meaning Devanagari, romanized, and Nepali–English queries. It will study retrieval robustness, not general translation quality or factual correctness beyond the supplied corpus. No BOUQuET/FLORES+ text or derivative is bundled.

## Record structure

Documents contain `doc_id`, `text`, `entity_id`, `provenance`, and `license`. Queries contain `query_id`, `group_id`, `text`, `variant`, `split`, `relevant_doc_ids`, `provenance`, and `license`. Provenance records origin, author ID, reviewer IDs, and review status. See the [protocol](docs/protocol.md) for review and split rules.

Benchmark-mode metadata checks do not authenticate humans or establish that linguistic review occurred. Future releases must document collection dates, language varieties, author/reviewer counts, consent, licenses, exclusions, disagreements, and adjudication. Use public pseudonym IDs; do not publish private consent records or contact details.

## Limitations and release conditions

There are no measured human-benchmark results, validated translations, confidence intervals, or representative sampling claims. Human records must have independent review, explicit publication permission, and compatible licensing before release. Each record's license governs that record; a software license does not automatically license future data.

Official community datasets have separate contribution and access conditions; see [community routes](docs/community-routes.md). Do not treat this starter as upstream endorsement or acceptance.
