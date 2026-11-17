---
name: wop
description: Create and manage self-contained, dependency-aware execution plans organized into strict sequential waves of mutually independent work. Use for planning, reviewing, revising, comparing, consolidating, auditing, archiving, restoring, or deleting durable project plans; do not use when the user asks to execute a project without planning it.
---

# Wave-Oriented Planning

Transform a request into a durable plan package whose waves execute in strict order and whose same-wave items are safe to run concurrently.

## Route the request

Identify one operation, then load only its route:

| Operation | Required references |
|---|---|
| CREATE | [creation](plan-management/creation.md); [principles](core/principles.md), [governance](core/governance.md), [adaptive planning](core/adaptive-planning.md), [planning process](core/planning-process.md), [wave method](core/wave-methodology.md), [dependencies](core/dependency-analysis.md), [acceptance](core/acceptance-criteria.md), and [traceability](core/traceability.md); [agent writing](writing/writing-for-agents.md) and [information hierarchy](writing/information-hierarchy.md); the selected template; applicable audits |
| DISCOVER or READ | [workspace](plan-management/workspace.md) and [discovery](plan-management/discovery.md) |
| REVIEW | [review](plan-management/review.md), [principles](core/principles.md), applicable audits, and only a relevant domain module |
| UPDATE | [revision](plan-management/revision.md); the CREATE Core and writing references; affected domain modules; validation and applicable audits |
| CONSOLIDATE | [revision](plan-management/revision.md), [principles](core/principles.md), [planning process](core/planning-process.md), [wave method](core/wave-methodology.md), [dependencies](core/dependency-analysis.md), [traceability](core/traceability.md), and relevant domain modules |
| COMPARE | [discovery](plan-management/discovery.md) and [review](plan-management/review.md) |
| AUDIT | [review](plan-management/review.md), [plan integrity](checklists/plan-integrity-audit.md), relevant audit checklists, and the affected integrity specifications |
| ARCHIVE or RESTORE | [workspace](plan-management/workspace.md) and [deletion/lifecycle](plan-management/deletion.md) |
| DELETE | [workspace](plan-management/workspace.md), [deletion](plan-management/deletion.md), and [plan integrity](checklists/plan-integrity-audit.md) |

Load [relationships](plan-management/relationships.md) only when the operation reads or changes plan relationships. Operations that only inspect or move stored plans do not need planning Core, writing, interaction, examples, or specialist modules.

For CREATE and UPDATE, select [compact](templates/compact-plan.md), [standard](templates/standard-plan.md), or [extensive](templates/extensive-plan.md) using adaptive planning. Translate every visible heading and prose block into the selected language while preserving structural marker IDs. The relocated [pt-BR](examples/localized-plans/pt-BR/standard-plan.md) and [Spanish](examples/localized-plans/es/standard-plan.md) plans demonstrate localization; they are not a language registry.

Apply conditional routing:

- Load [Decision-Focused Clarification](interaction/grilling.md) and the [question strategy](interaction/question-strategy.md) only when unresolved user-owned decisions materially change the plan.
- For software, load [the code module](modules/code/module.md), then security, performance, or testing only when applicable.
- For documents, load [the documents module](modules/documents/module.md), editorial quality when relevant, and only the required format module. Never load every format module by default.
- For a genuinely new recurring domain, use [the extension guidance](modules/future-domains/README.md) and [module contract](specifications/module-contract.md).
- Load an example only to resolve a specific ambiguity or demonstrate a relevant pattern; do not treat examples as normative catalogs.
- Do not load every checklist. Use [adaptive planning](core/adaptive-planning.md) to select essential, complete, or detailed audit depth while keeping universal invariants mandatory.

## Documentation responsibilities

- Core defines WOP and its mandatory planning rules.
- Interaction governs unresolved user decisions.
- Writing governs communication to execution agents.
- Modules add domain-specific requirements.
- Plan Management governs persistent artifact operations.
- Templates define output structures; checklists verify compliance; scripts automate deterministic operations; examples demonstrate application.

## Preserve these invariants

- README.md is authoritative plan content; SQLite is the operational index.
- Wave N+1 cannot begin until every item in Wave N is completed, individually accepted, integrated where needed, and the wave gate passes.
- Same-wave items have no unmet dependency or shared-write interference.
- Every material requirement maps to responsible work and measurable evidence.
- The global execution protocol contains only rules applicable to every wave. Put item assignments, parallelism, ownership, outputs, and wave-only restrictions in each wave's `execution_instructions` field.
- Custom `wop:section` context is global by default; use `scope=wave waves=...` or `scope=item items=...` only to narrow propagation, and verify every selector.
- In the selected language, the execution protocol tells the orchestrator to identify the package, read `README.md` and every referenced prompt, execute waves in order, block premature advancement, integrate results, evaluate each completion gate, and perform final acceptance.
- Facts, decisions, assumptions, and unknowns remain distinct.
- Use the fewest waves, items, and agents that preserve independence, verification, and risk control. One wave and one item are valid; never fragment work for appearance or utilization.
- Compact may omit irrelevant sections and optional fields, but never objectives, acceptance criteria, strict sequencing, prompt consistency, direct coverage, final acceptance, or integrity.
- Never invent inspection results, execution evidence, acceptance, or inaccessible facts.
- Permanent deletion requires explicit confirmation immediately before deletion.

## Language

Write the skill internals and technical identifiers in English. Select the plan language by this strict hierarchy: the user’s explicit language request; otherwise the conversation’s predominant language; otherwise English only when the language is genuinely unclear. Accept any structurally valid BCP 47-style tag the agent can write—never restrict selection to a built-in locale list.

Write every linguistic part of the plan in that language: title, visible headings, prose, requirements, criteria, gates, evidence instructions, handoffs, revision history, wave prompts, and `execute-all.md`. Keep only technical IDs, paths, filenames, code, commands, protocol tokens, and user-supplied technical terms unchanged. Preserve `wop:*` markers because they carry structure independently of visible wording.

Prompt generation is language-neutral and does not translate or inject locale-specific prose. It composes prompts losslessly from the selected-language README and verifies the exact rendering. When changing a plan’s language, rewrite all linguistic content, update the metadata tag and version, regenerate the complete prompt directory, synchronize SQLite, and confirm that no obsolete-language prose remains.

## Workspace tools

Initialize a project workspace with scripts/init_workspace.py. Generate prompts and validate a package with scripts/validate_plan.py --generate-prompts. Register and manage packages with scripts/wop_db.py. Read [specifications/plan-ir.md](specifications/plan-ir.md), [plan-management/workspace.md](plan-management/workspace.md), and [README.md](README.md) for structural IDs, exact commands, exit codes, and recovery behavior.

For CREATE, inspect existing plans before deciding the request is new. Do not set plan_status to ready until README.md, every wave prompt, execute-all.md, mechanical validation, and the semantic audits all pass. Deliver the title, stable ID, current path, version, language, status, and validation result.

For READ, REVIEW, COMPARE, and AUDIT, do not modify artifacts unless the user separately requests changes. For UPDATE, preserve plan_id and created_at, increment version for content changes, rename the package, regenerate affected prompts, update SQLite, and revalidate.
