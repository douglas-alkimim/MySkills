# WOP Correction and Hardening Report

## Final usability refinement — 2026-11-16

- Reduced the official Compact scaffold from 160 to 80 lines, 15 to 7 plan sections, and 20 to 8 wave/item fields while preserving metadata, direct requirement coverage, strict sequencing, prompts, verification, final acceptance, and revision history.
- Made structural requirements complexity-aware: Compact requires the essential contract and conditionally requires independence/ownership fields when items coexist; Standard and Extensive retain their complete field sets.
- Added explicit Compact, Standard, and Extensive audit profiles to validation output without changing universal correctness invariants.
- Reworked `SKILL.md` into operation-specific reference routes so READ/DISCOVER and lifecycle operations do not load unrelated planning, writing, interaction, checklist, example, or specialist material.
- Relocated pt-BR and Spanish standard plans from official templates to `examples/localized-plans/`, preserving structural markers and open language support.
- Established the anti-fragmentation rule across Core, templates, checklists, and examples: one wave and one item are valid, and splitting must improve independence, verification, or risk.
- Expanded the forward behavior catalog from 18 to 23 cases and the automated suite from 37 to 43 tests.

## Prompt scope and context propagation revision — 2026-11-15

- Separated the universal global protocol from current-wave execution instructions.
- Replaced repeated execution-boundary, predecessor, full-wave, and completion copies with five non-overlapping prompt blocks.
- Added explicit technical authorization metadata and exact assigned-item markers to every wave prompt.
- Added deterministic checks for global item assignments, foreign item instructions, self/future dependencies, later-wave execution references, ownership conflicts, and prompt assignment drift.
- Extended `wop:section` with `scope=global`, `scope=wave waves=...`, and `scope=item items=...`; unscoped custom sections default to global.
- Propagated global custom context to every wave and `execute-all.md`, while wave/item context reaches only selected wave prompts.
- Corrected and regenerated both complete example packages from their READMEs.
- Added three-wave assignment, exact custom-scope propagation, and intentional contradiction regression coverage.

## Universal internationalization revision — 2026-11-15

- Removed the runtime locale catalog and every generated-language fallback.
- Added deterministic language selection semantics: explicit user request, then predominant conversation language, then English only when unclear.
- Accepts open, structurally valid BCP 47-style tags without a closed registry.
- Prompt generation now derives every visible instruction, heading, criterion, gate, evidence requirement, and handoff from the localized README; only technical metadata, IDs, references, and structural markers are injected.
- Made canonical wave and item templates universally translatable through invisible markers; pt-BR and Spanish templates remain examples rather than a support boundary.
- Made technical ID discovery safe next to Latin, CJK, Arabic, and other scripts.
- Added coverage for pt-BR, en, es, fr, de, ja, zh-CN, ar, Esperanto as an unregistered runtime language, language changes, multilingual revisions, and mixed technical literals.

## Scope

This revision strengthens the existing modular implementation without removing its planning, interaction, writing, specialist-module, workspace, SQLite, prompt, lifecycle, or testing architecture.

## Wave 1 — Data integrity

- Formalized authority boundaries: README for editorial plan content, prompt files for execution instructions, and SQLite for stable identity, path/name, operational states, evidence, operations, relations, revisions, events, and tombstones.
- Made rebuild preserve registered operational states and history, report stale README projections, initialize missing execution/acceptance state conservatively, and reject tombstoned or duplicate identities.
- Made archive/restore preserve the prior plan state, execution/acceptance state, stable ID, complete package, and editorial timestamp.
- Expanded audit results to `valid`, `invalid`, `unchecked`, `missing`, and `conflict`; unchecked work never passes.
- Added produced-evidence references with summary, actor, and optional human approval. Executed/completed/accepted transitions are evidence-gated.
- Added recoverable operation records and compensation for status, rename, archive, restore, and delete failure paths.

## Wave 2 — Internationalization and prompts

- Added `scripts/plan_model.py`, a language-neutral intermediate representation with invisible structural markers and backward-compatible English, Portuguese, and Spanish aliases.
- Originally added generated-instruction locale bundles for English, Portuguese, and Spanish; the universal internationalization revision above removed this closed catalog.
- Generated prompts now include relevant global context, complete assigned work, and explicit predecessor producers, outputs, evidence, criteria, gates, and handoff.
- Prompt generation stages a complete directory, swaps it safely, restores the old set on failure, and removes obsolete prompts.
- Added localized pt-BR and Spanish standard examples plus structural markers to canonical templates.

## Wave 3 — Governance and security

- Rejects new `depends_on` cycles and audits preexisting cycles without treating associative relations as dependencies.
- Distinguishes editorial revision from administrative rename; content revision preserves identity/creation time, requires exactly one version increment and a changed editorial timestamp, regenerates prompts, records history, and compensates on failure.
- Added explicit initial-filesystem, database-step, rollback, interrupted-operation, and delete-cleanup recovery reporting.
- Removed Python 3.9-incompatible file-writing usage and verified the complete suite on Python 3.9.25 and a modern runtime.
- Made documentation host-neutral and routing selective while retaining mandatory Core and agent-writing baselines.
- Hardened path resolution, CLI generation boundaries, overwrite guards, parameterized SQL, IDs, destructive confirmation, JSON errors, and exit codes.

## Wave 4 — Homologation

- Expanded the original nine tests to 27 end-to-end regression tests.
- Added 18 documented behavioral acceptance cases.
- Added complete validated English and pt-BR example packages with three waves, a parallel item pair, four generated prompts, traceability, predecessor gates, and revision history.
- Added automated example lifecycle coverage for register, query, revision, regeneration, archive, restore, audit, and confirmed delete.
- Added `tests/homologation-report.md` with executed commands, results, coverage, and explicit limitations.

## Compatibility

Legacy English plans continue to parse without markers. Known Portuguese and Spanish headings also have compatibility aliases. Structural comments are the universal mechanism for translated or custom visible headings in any language. No runtime dependency beyond the Python standard library was added.

## Remaining limitations

- Mechanical checks cannot prove semantic independence, requirement sufficiency, or acceptance implication; the documented semantic audits remain mandatory.
- Mechanical validation cannot identify a natural language semantically; it proves that prompts exactly preserve and compose the declared-language README, while the documented semantic language audit distinguishes prose from legitimate technical literals.
- Filesystem and SQLite cannot share one transaction. Operations are compensating and auditable, not jointly atomic; a process or machine crash can still require the explicit recovery steps reported by `check`.
- If the SQLite database and its backups are truly lost, rebuild cannot reconstruct produced execution/acceptance evidence from a README projection. It resets those dimensions conservatively and reports conflicts instead of inventing evidence.
- The 23 behavioral cases are forward tests for execution against fresh agent sessions. Their catalog and routing assertions are validated here, but this repository suite does not launch 23 external agent sessions.
