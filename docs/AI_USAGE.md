# Use of Artificial Intelligence

> Required by NASA Space Apps: state where and how AI was used. AI-generated images/videos carry a visible label; AI content never contains or alters NASA branding.

| Date | Stage | Tool | What was generated / assisted | Human review |
|---|---|---|---|---|
| 2026-11-14 | 0 | Claude Code (Anthropic, Claude Opus) | Repository skeleton, module stubs, documentation templates, resource summaries in RESEARCH_LOG.md | Ruslan Sharafutdinov (decisions, review) |
| 2026-11-14 | 2 | Claude Code (Anthropic, Claude Opus) | PSI/NTRS data reconnaissance, fetch script, candidate assessment in DATA_SOURCES.md | Ruslan Sharafutdinov (dataset decisions ADR-012..014) |
| 2026-11-14 | 3 | Claude Code (Anthropic, Claude Opus) | Data-layer code (parsers, cleaning, schema, build, tests), PDF cross-check script, EDA figures, data documentation | Ruslan Sharafutdinov (anomaly, CV-group and target decisions ADR-015..018) |
| 2026-11-14 | 4 | Claude Code (Anthropic, Claude Opus) | Physics-layer code, NIST fetch script, theory-vs-data comparison and figures, PHYSICS.md | Ruslan Sharafutdinov (theory level, property assumptions, gravity base, feature set ADR-022..025) |
| 2026-11-14 | 4 | Claude Code (Anthropic, Claude Opus) | L&W prescription implementation, Svehla transcription, Cantera flame temperature, PHYSICS.md rewrite | Ruslan Sharafutdinov (supplied L&W paper; ADR-026, ADR-027) |
| 2026-11-14 | 5 | Claude Code (Anthropic, Claude Opus) | Model code (hybrid GP, classifiers), CV comparison, interpretation, MODEL_CARD.md | Ruslan Sharafutdinov (ADR-029 choices) |
| 2026-11-14 | 6 | Claude Code (Anthropic, Claude Opus) | Validation code, variant selection, reliability rule, generated VALIDATION.md | Ruslan Sharafutdinov (ADR-030..032) |
| 2026-11-14 | 7 | Claude Code (Anthropic, Claude Opus) | Insight functions, ranking, INSIGHTS.md generator, insight tests | Ruslan Sharafutdinov (ADR-033: catalog, formula, wording) |
