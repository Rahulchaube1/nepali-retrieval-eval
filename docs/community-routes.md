# Community contribution routes

Reviewed 26 November 2026. This project is independent of Meta, BOUQuET, OLDI, and FLORES+. It is not an accepted contribution or an official benchmark extension.

## BOUQuET

The [official dataset](https://huggingface.co/datasets/facebook/bouquet) already lists Nepali as `npi_Deva`. The [Space](https://huggingface.co/spaces/facebook/bouquet) directs translation and validation contributions to [bouquet.metademolab.com](https://bouquet.metademolab.com/). Availability of particular tasks must be checked in that portal.

The [contributor guidelines](https://huggingface.co/spaces/facebook/bouquet/blob/main/app.py) prefer native target-language users and strong source-language proficiency. They prohibit AI-generated translations, translation software, and automated suggestions; dictionaries are allowed. Preserving meaning, tone, and register requires human work. The portal requires a Meta Individual Contributor License Agreement. Contributors must review and complete that step themselves; this repository neither signs agreements nor submits translations automatically.

BOUQuET is labeled CC BY 4.0, with additional [access conditions](https://huggingface.co/datasets/facebook/bouquet/blob/main/README.md): evaluation use, no model training on the data or derivatives, protected/private redistribution, and retention of those conditions. Obtain access through the official account flow. Do not bundle benchmark texts or derived versions in a public repository.

## FLORES+ and OLDI

[OLDI's language list](https://oldi.org/languages) already includes Nepali (`npi_Deva_nepa1254`). Follow its [contribution guidelines](https://oldi.org/guidelines): coordinate with organizers before starting, establish the language variety, document authoring and quality assurance in a dataset card, and obtain participants' acknowledgments.

The [translation rules](https://oldi.org/translation-guidelines.pdf) require human evaluation translations; even referencing or post-editing machine translation is normally disallowed. Discuss any exception with the organizers first.

[FLORES+](https://huggingface.co/datasets/openlanguagedata/flores_plus) uses CC BY-SA 4.0 and gated evaluation-integrity conditions. Its official workflow uses a Hugging Face pull request and a DCO sign-off. Review the current requirements and make only truthful declarations; this project performs neither step automatically. Access and upstream acceptance remain separate from publishing this starter.
