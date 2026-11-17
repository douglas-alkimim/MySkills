# Status Model

Status dimensions are independent.

## plan_status

- draft: incomplete or not yet fully validated.
- ready: complete, synchronized, and validated for execution.
- in_progress: plan is actively being executed or revised.
- blocked: plan-level progress cannot continue.
- completed: planned work is complete; acceptance may remain pending.
- accepted: final acceptance was established with evidence.
- cancelled: intentionally stopped.
- superseded: another plan replaces its applicable scope.
- archived: preserved outside the active plans directory.

## execution_status

- not_started
- in_progress
- partially_executed
- blocked
- executed
- abandoned

## acceptance_status

- not_evaluated
- pending
- accepted
- rejected

Executed does not imply accepted. `execution_status=executed` and `plan_status=completed` require an identifiable execution-evidence reference. `acceptance_status=accepted` and `plan_status=accepted` require an acceptance-evidence reference; record a human approver when governance requires one. Planned evidence in a README is not produced evidence.

Archive is an administrative storage state, not an execution result. Archiving records the prior `plan_status` while preserving execution and acceptance. Restore returns to that prior status and does not alter the editorial `updated_at`. A restored package still has to pass integrity checks before new execution.

SQLite is authoritative for all three operational status dimensions. README front matter carries their synchronized projection for portability; rebuild reports a stale projection and preserves the indexed value.
