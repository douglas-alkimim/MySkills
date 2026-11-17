# Review, Compare, and Audit

These operations are read-only unless the user separately requests a repair.

## Review

Evaluate outcome clarity, scope, facts/assumptions/unknowns, requirement coverage, dependency graph, wave barrier, pairwise independence, ownership, acceptance implication, verification, governance, language consistency, and prompt self-containment.

## Compare

Compare versions or plans by identity, scope, requirements, decisions, contracts, waves, items, dependencies, ownership, criteria, prompts, statuses, relations, and unresolved risks. Distinguish additions, removals, changes, and unchanged content. Do not consolidate merely because plans overlap.

## Audit

Run validate_plan.py and wop_db.py check, then apply the semantic checklists at the plan's declared complexity. Compact uses essential planning/writing checks and direct coverage; Standard uses complete checks and a traceability matrix; Extensive adds detailed risk, recovery, traceability, and isolation analysis. Universal invariants do not vary. Report evidence, severity, affected artifact, and recommended correction for findings; a concise pass summary is sufficient when a simple plan has no issue. Mechanical success does not prove plan quality.
