# Governance

## State control

Keep plan, execution, and acceptance states independent. Follow specifications/status-model.md. Transition only from actual evidence and record material transitions as events.

## Blockers and failures

Stop affected work when a predecessor gate fails, required input is absent, ownership conflicts, or an unapproved scope change is needed. Record the blocker, affected items, evidence, safe state, and decision required. Do not bypass the wave barrier.

## Change control

Content changes preserve the stable plan ID, increment version, retain created_at, update updated_at, rename the package, record revision history, regenerate affected prompts, update SQLite, and rerun validation. Administrative status changes need events but do not require content-version inflation.

## Authorization

Planning does not authorize execution, deployment, messaging, purchases, production changes, or destructive actions. Preserve the user’s existing authority boundaries. DELETE requires explicit confirmation of the exact plan immediately before the CLI action.

## Integrity failures

When filesystem and SQLite disagree, stop lifecycle mutations, run check, identify the authoritative README and actual package location, then repair or rebuild. Never invent missing metadata, silently reuse a tombstoned ID, or discard revision evidence.
