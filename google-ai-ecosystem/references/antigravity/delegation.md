# Delegation and Integration

Antigravity is the default external worker for meaningful repository engineering, but not every local task needs delegation or multiple agents.

## Choose the role

| Role | Good use | Default | Local-agent follow-up |
|---|---|---|---|
| Explorer | Locate interfaces, dependencies, or likely causes | `plan`, no writes | Confirm cited files/behavior |
| Planner | Architecture, migration, or implementation plan | `plan`, no writes | Reconcile with actual dependencies and user constraints |
| Reviewer | Challenge a diff/design/test plan | `plan`, no writes | Triage each finding with evidence |
| Verifier | Execute named checks in bounded scope | Headless only with pre-scoped permissions | Re-run critical checks and inspect raw output |
| Implementer | Make a user-authorized repository change | Serial execution in exact write scope | Review every changed/untracked file and tests |
| Coordinator | Independent multi-agent workstreams | Non-overlapping ownership/worktrees | Integrate in dependency order |

Do not delegate trivial work, coupled work that cannot be isolated, or tasks where context/cost outweighs decision value.

## Prompt contract

```text
Role: Act as an independent <role>.
Goal: <one concrete outcome>.
Workspace: <resolved directory>.
Scope: <allowed reads, exact writes, commands/network, and exclusions>.
Context: <minimum authoritative facts and artifacts>.
Deliverable: <result shape with file/evidence/uncertainty>.
Verification: <named checks and acceptance criteria>.
Stop: stop before work outside scope; report missing context instead of guessing; preserve unrelated changes.
```

For adversarial review, request counterexamples, tight file/line evidence, severity, and a minimal repair without revealing a desired verdict.

## Integration

Before a write delegation, record the existing working tree and ensure no overlapping writer. Afterward, inspect the complete diff, reject unrelated changes, and rerun critical checks under local control. Antigravity's `SUCCESS` proves only its validated terminal result, not the correctness of its claims.

## Hybrid handoff

For research→implementation, Gemini produces a source-backed specification and Antigravity implements named repository changes. For repository→media, Antigravity produces a concise product/visual specification and Gemini generates the asset. Name the artifact and direction; do not run both without a necessary handoff.

