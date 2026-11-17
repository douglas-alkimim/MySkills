# Multi-Agent Planning Overlay

Apply this overlay to a complete compact, standard, or extensive plan. It does not replace required plan sections.

Use it only when independent ownership and critical-path benefit exceed dispatch, synchronization, review, and integration overhead. Do not create agents or items merely to fill the matrix.

## Agent Execution Model

- Orchestrator: <responsibility and authority>.
- Maximum useful concurrency: <number or environment-dependent>.
- Dispatch unit: one complete item with its standalone wave context.
- Shared-state rule: <branch, worktree, document, database, or service isolation>.
- Integration owner: <owner>.
- Conflict policy: stop, preserve both outputs, and escalate; do not overwrite another owner’s work.

## Assignment Matrix

| Wave | Item | Owner role | Exclusive scope | Inputs | Output | Report channel |
|---|---|---|---|---|---|---|
| W001 | I001 | <role> | <files/artifacts/effects> | <inputs> | <output> | <handoff> |

## Dispatch Contract

Each agent receives plan ID/version/language; authorized and non-authorized item IDs; blocked successor waves; the item-agnostic global protocol; current-wave execution instructions; scoped context and contracts; predecessor evidence; exact ownership, outputs, restrictions, criteria, verification, and report format. Agents execute only the released wave and never modify plan scope.

## Join and Integration Gate

The orchestrator waits for every item. It verifies reports and evidence, detects cross-item conflicts, integrates in the stated order, runs integration checks, and evaluates the wave gate. Missing or failed work blocks the entire next wave.

## Agent Report

- Item ID and outcome.
- Changed files or artifacts.
- Tests/checks and actual results.
- Acceptance evidence.
- Deviations and risks.
- Blockers.
- Handoff outputs.

## Failure and Reassignment

<Retry limit, preserved state, reassignment rule, and when human input is required. Reassignment does not weaken criteria or ownership controls.>
