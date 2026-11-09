# Complete official post context review

The user has authorized automated batch decisions with body evidence, immediate admission of clear passes, exception isolation and reuse of unchanged source checks. This correction implements that existing scope; it does not expand the thesis topic or the source authenticity gate.

Problem: a complete short institutional post can state China's nuclear buildup or trade strategy in one paragraph and the American response in another. Requiring every cue in one paragraph creates false negatives. Joining separate documents, using references or trusting a country mention would create false positives.

Design: retain current filters and same-paragraph decisions. A fallback applies only to complete institutional platform posts with an established source, platform identity and at most 2,000 characters. Independently require a China paragraph with policy/security content and a US paragraph that explicitly identifies China with policy/security content. A country-only paragraph cannot satisfy either anchor; two independent China/Brazil and US/Canada trade topics do not qualify. Save the unchanged full post with exact offsets and SHA as the supporting passage. Do not apply the fallback to articles, research papers, unknown accounts, audiovisual promotions, unresolved earlier metadata concerns or partial texts. Actual source completeness, date and ownership still require the existing independent audit.

Alternatives considered: retaining same-paragraph-only matching misses explicit post context; allowing arbitrary document-wide keyword co-occurrence admits unrelated references. The bounded complete-post fallback preserves document identity and narrow thematic evidence.

- [x] Add synthetic split-paragraph trade and nuclear examples that currently fail, alongside unrelated-country, unknown-source, oversized-post, promotional and research exclusions.
- [x] Run tests to establish the expected failure; implement only the bounded fallback in `batch_review.py` and verify exact passage offsets and body-supported derived fields.
- [x] Run the full local suite. Reassess only previously source-passed negative posts, preserve previous states and decision manifests, then apply independent source/field gates and export all nine fields.
- [ ] Report actual changed formal counts and exceptions; preserve all source evidence locally and publish only code, synthetic tests and aggregate results.

Validation: the initial positive scenarios failed before implementation; a separate two-unrelated-trade-topics regression also failed before the explicit US/China anchor was added. All 599 local tests pass. Source validation implementation is unchanged, so valid source cache entries remain usable.
