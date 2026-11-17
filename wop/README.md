# WOP — Wave-Oriented Planning

WOP is one of the independently usable skills in MySkills. It creates and manages execution plans as strictly ordered waves. Work items inside one wave may execute concurrently only when their dependencies, ownership, and mutable resources are independent.

## Contents

- SKILL.md: concise invocation and routing instructions.
- LICENSE: the MIT terms for independent distribution.
- core/: planning method, wave construction, dependencies, acceptance, traceability, adaptation, and governance.
- interaction/: clarification, question-frontier, decision, unknown, and prototype guidance.
- writing/: agent-facing editorial standards.
- modules/: code and document specialists plus an extension contract.
- plan-management/: workspace and lifecycle operations.
- templates/: official language-neutral structural templates plus multi-agent, change, handoff, and history templates.
- checklists/: mechanical and semantic audits.
- specifications/: schemas, statuses, naming, workspace, and module contracts.
- scripts/: Python 3.9+ standard-library tooling.
- examples/: representative patterns, localized pt-BR and Spanish plan examples, and complete validated English and pt-BR packages with generated prompts. Localized examples demonstrate universal language support; they do not define a language catalog.
- tests/: end-to-end unittest coverage.

## Installation

This repository copy is intentionally not installed. To install later in any compatible agent host, copy the complete `wop` directory into that host's skill directory without changing its internal structure. The scripts also work directly from a checkout and require no Python packages.

## Quick start

Use a Python 3.9+ interpreter.

    python path/to/wop/scripts/init_workspace.py --root /path/to/project

Create a package under:

    PROJECT/.wop/plans/YYYY_MM_DD_hh_mm_ss-plan_name/README.md

Start from templates/standard-plan.md for ordinary multi-deliverable work. Use compact for bounded low-risk work and extensive only when risk, uncertainty, systems, external effects, reversibility, or coordination justify it. A one-wave, one-item plan is valid; never add work units merely to make a plan look sophisticated. Then generate synchronized prompts and validate:

    python path/to/wop/scripts/validate_plan.py \
      --root /path/to/project \
      --directory .wop/plans/PACKAGE \
      --generate-prompts

After mechanical and semantic audits pass, register the package:

    python path/to/wop/scripts/wop_db.py \
      --root /path/to/project \
      register --directory .wop/plans/PACKAGE

Global --json must appear before the subcommand.

## Database commands

The CLI supports list, search, get, relations, relate, history, evidence, check, rebuild, register, rename, set-status, archive, restore, and delete. Run scripts/wop_db.py --help and the selected subcommand with --help for current arguments. Commands return exit code 0 on success and 2 for invalid arguments, rejected operations, failed integrity reports, or recoverable operational errors. Put `--json` before the subcommand for machine-readable stdout; errors are JSON on stderr.

Examples:

    python path/to/wop/scripts/wop_db.py --root PROJECT list
    python path/to/wop/scripts/wop_db.py --root PROJECT search --query authentication
    python path/to/wop/scripts/wop_db.py --root PROJECT get --id UUID
    python path/to/wop/scripts/wop_db.py --root PROJECT check
    python path/to/wop/scripts/wop_db.py --root PROJECT rebuild
    python path/to/wop/scripts/wop_db.py --root PROJECT evidence --id UUID
    python path/to/wop/scripts/wop_db.py --root PROJECT set-status --id UUID \
      --execution-status executed --plan-status completed \
      --evidence-reference reports/test-results.json \
      --evidence-summary "All planned checks passed" --actor release-agent
    python path/to/wop/scripts/wop_db.py --root PROJECT archive --id UUID
    python path/to/wop/scripts/wop_db.py --root PROJECT restore --id UUID
    python path/to/wop/scripts/wop_db.py --root PROJECT delete --id UUID --confirm

DELETE is permanent. The CLI refuses it without --confirm, refuses deletion when another plan depends on the target, removes the complete package, and retains a tombstone plus deletion event.

## Prompt generation

validate_plan.py parses the authoritative README into a language-neutral intermediate representation, generates one standalone wave-NN.md per wave, removes stale wave prompts, and generates prompts/execute-all.md. Generation has no locale catalog, language branch, or translation fallback: all visible prompt content is composed from the selected-language README, while technical metadata and structural markers remain stable. The global protocol is emitted once; current-wave execution scope, predecessor verification, shared context, and completion contracts have distinct non-overlapping blocks. Prompt front matter names authorized and non-authorized items and blocked successor waves. It writes a complete prompt set to a temporary sibling directory and swaps it into place; a staging failure leaves the active prompt set unchanged. Every generated file contains plan identity, version, language, source path, and a source README SHA-256. Content, language, or version changes make old prompts mechanically stale until regeneration; operational status projections do not change the editorial digest.

Custom level-two sections use the existing marker contract. Omitted scope defaults to global and reaches every wave prompt plus `execute-all.md`; `scope=wave waves=W002,W003` and `scope=item items=I004,I005` narrow propagation. Nonexistent selectors and malformed scope attributes fail validation. See specifications/plan-ir.md for the complete grammar and propagation contract.

Mechanical validation covers package naming, open BCP 47-style language tags, complexity-appropriate structural requirements, sequential wave IDs, item fields, exact item assignment, global-protocol contamination, forward dependencies, execution-instruction and ownership conflicts, custom context selectors, prompt identity and source hash, exact source-derived rendering, predecessor outputs/evidence/gates, orchestration references, path existence, and optional SQLite consistency. Visible headings may use any language the agent can write; invisible structural markers keep parsing language-neutral. The report declares the Compact, Standard, or Extensive audit profile while preserving universal correctness checks. See specifications/plan-ir.md. It also lists the proportional semantic review an agent must perform; textual checks cannot prove every natural-language meaning, independence, coverage, or acceptance implication.

## Tests

Run:

    python -B -m unittest discover -s path/to/wop/tests -v

Tests use temporary workspaces and leave no database, cache, compiled file, or test plan in the skill package.

The complete packages under `examples/packages/` each contain three waves, four items (including an independent same-wave pair), three individual prompts, execute-all.md, traceability, predecessor gates, and revision history. The automated suite copies both packages into a temporary workspace and demonstrates validation, registration, query, versioned update, prompt regeneration, archive, restore, and confirmed deletion without modifying the shipped examples.

## Authority and recovery

Markdown is authoritative for plan content and prompt files are authoritative for generated execution instructions. SQLite is authoritative for stable identity, current path/name, administrative, execution and acceptance states, evidence references, operations, relations, revisions, events, and tombstones. README status fields are synchronized projections and never override a newer indexed state during rebuild. Filesystem and SQLite changes cannot be one transaction; lifecycle commands record an operation, move or rename safely, and compensate when a later step fails. If a crash still leaves disagreement, run check, inspect pending/failed operation details and exact paths, repair ambiguity without discarding either copy, then run rebuild. Rebuild preserves registered operational history, never invents execution evidence, and rejects tombstoned IDs.

## Conceptual influences

WOP incorporates two independent ideas without depending on external skills: agent-facing writing should minimize no-op text while strengthening information hierarchy and completion criteria; clarification should ask only decision questions whose prerequisites are resolved and should turn investigable uncertainty into discovery work.

## License

WOP is available under the [MIT License](LICENSE).
