# Plan Intermediate Representation

The validator converts `README.md` into a small, standard-library-only intermediate representation before generating prompts. Visible Markdown remains readable and translatable; stable IDs identify semantics independently of the heading language.

## Structural markers

Place an optional HTML comment at the end of a heading:

```markdown
## Resultado <!-- wop:section outcome -->
## Decisões de Arquitetura <!-- wop:section architecture_decisions scope=global -->
## Migração <!-- wop:section database_migration scope=wave waves=W002,W003 -->
## Restrição Especial <!-- wop:section special_restrictions scope=item items=I004 -->
## Onda W001 — Descoberta <!-- wop:wave W001 -->
### Objetivo Geral <!-- wop:field general_objective -->
### Instruções de Execução da Onda <!-- wop:field execution_instructions -->
#### Item I001 — Inspecionar <!-- wop:item I001 -->
##### Critérios de Aceite <!-- wop:field acceptance_criteria -->
```

Markdown renderers hide the comments. Technical IDs stay in English even when visible headings are translated. New templates must carry markers on semantic sections, waves, items, and fields. Legacy English, Portuguese, and Spanish headings remain supported through compatibility aliases, so existing packages do not require immediate migration; those aliases are not a language catalog.

Marker kinds are:

- `section`: a plan-level semantic section such as `outcome`, `risks`, `global_contracts`, `rollback_recovery`, or `final_acceptance`.
- `wave`: a sequential `WNNN` entity.
- `item`: a globally unique `INNN` work item.
- `field`: a wave or item field such as `prerequisites`, `outputs`, `completion_gate`, or `verification_evidence`.

Do not translate or reuse marker IDs. Preserve them during revision, translation, consolidation, and template customization.

## Custom section scope

Custom plan sections extend the existing `wop:section` marker; they do not introduce a second markup language. Supported attributes are space-separated `key=value` tokens:

- No `scope` attribute, or `scope=global`: include the complete section in every wave prompt and in `execute-all.md`.
- `scope=wave waves=W002,W003`: include it only in the named wave prompts.
- `scope=item items=I004,I005`: include it only in prompts for waves containing a named item.

Selectors are comma-separated technical IDs. Global sections cannot declare selectors; wave scope requires `waves=`; item scope requires `items=`. Unknown attributes, malformed scopes, missing selectors, and nonexistent IDs fail validation. Unmarked custom level-two sections also default to global so context is never silently discarded. Standard WOP sections remain global.

## IR contents

`scripts/plan_model.py` preserves metadata, title, recognized and custom plan sections, custom scope/selectors, waves, work items, fields, raw Markdown, warnings, and references among `RNNN`, `WNNN`, and `INNN` IDs. Prompt generation uses this model to include global and selected context, current-wave authorization, and explicit predecessor producers, outputs, evidence requirements, criteria, gate, and handoff.

Required plan, wave, and item IDs are exported by `plan_model.py` and enforced by `validate_plan.py`. This makes validation structural rather than a fixed English-heading check.

Required fields are complexity-aware. Compact enforces the essential plan, wave, and item contract and conditionally requires independence and ownership fields when items coexist. Standard enforces its ordinary-project core while allowing genuinely irrelevant fact, assumption, unknown, and contract sections to be omitted. Extensive retains the complete structural contract. This changes documentation depth, not prompt identity, sequencing, acceptance, or lifecycle behavior.

## Prompt composition contract

The global `execution_protocol` is item-agnostic and appears once in every wave prompt. Each newly authored wave adds `execution_instructions` containing only its assigned items, allowed parallelism, ownership, outputs, restrictions, and integration behavior. Legacy plans without this field remain parseable: the generator derives an explicit scope from the wave and item fields, while semantic review must confirm the intended execution behavior.

Each wave prompt contains five non-overlapping primary blocks:

1. `global_protocol`: rules applicable to every wave.
2. `execution_scope`: the current wave's objective, requirements, execution instructions, parallelism, ownership, and assigned item objectives/inputs/scope/outputs/restrictions.
3. `predecessor_verification`: prerequisites plus predecessor outputs, evidence, criteria, gates, and handoffs.
4. `shared_context`: standard global context plus custom sections selected for this wave.
5. `completion_contract`: current-wave and item criteria, evidence, gate, integration, and handoff.

Front matter records `authorized_items`, `non_authorized_items`, `predecessor_waves`, and `blocked_successor_waves`. Assigned-item markers must exactly match the current wave. `execute-all.md` contains all global standard and custom context and references non-global context through the wave prompts rather than duplicating it.

Deterministic validation rejects item IDs in the global protocol, current-wave instructions that name a different item set, self/future/unknown prerequisite waves, later-wave references in wave execution instructions, incompatible ownership references, invalid custom selectors, and assigned-item prompt markers that differ from the IR. Exact source-derived prompt comparison detects manual or stale prompt changes. Semantic review remains responsible for contradictions whose meaning depends on natural language, including indirect authorization, negation, or ambiguous ownership prose.

## Language behavior

The plan front matter records any structurally valid BCP 47-style language tag; validation does not consult a closed registry. The authoring agent selects the explicit user-requested language first, otherwise the conversation’s predominant language, and uses English only when the language is unclear.

The generator has no translation catalog and never invents natural-language scaffolding. It composes the global protocol, current-wave execution scope, predecessor verification, scoped shared context, completion contract, and orchestration content directly from the README’s localized structural sections. Therefore any language the agent can author works without a code change. All prompts retain the original language tag, paths, and technical identifiers.

The authoring agent is responsible for using the selected language consistently in the title, visible headings, prose, requirements, criteria, gates, evidence, handoffs, revision history, and instructions. Code, commands, API names, acronyms, IDs, paths, filenames, and user-supplied technical terms remain literal and must not trigger a false mixed-language finding. Mechanical validation proves exact source-derived rendering, not semantic language identification; the semantic language audit remains mandatory.

The validation report exposes an `audit_profile`. Compact uses essential planning and writing checks plus direct coverage; Standard uses complete checks and a traceability matrix; Extensive adds detailed planning, full traceability, and isolation, risk, and recovery evidence. The universal invariant list is identical for every profile.

A language change is an editorial revision: preserve `plan_id` and `created_at`, increment the version, update `updated_at`, rewrite all linguistic content, regenerate the entire prompt set, synchronize SQLite, and verify that obsolete-language prose is gone.

## Synchronization and recovery

Every prompt records `plan_id`, `plan_version`, `language`, and `source_readme_sha256`. The digest excludes only the three SQLite-authoritative operational status projections. Editorial content, version, language, criteria, requirements, and dependencies affect the digest.

Generation writes a complete set into a temporary sibling directory, verifies its filenames, swaps directories, and restores the old set if the swap fails. A successful run removes obsolete wave prompts. If old-backup cleanup alone fails, the new prompts remain active and the error names the backup requiring cleanup.
