# Example: Software Project

Request: add tenant-aware API key authentication to an existing service.

## Investigation

Inspect the framework, request pipeline, database schema, migration system, configuration, existing identity model, tests, deployment, and logging. Ask only decisions not answered by the code, such as key expiry policy or user-visible revocation behavior.

## Wave shape

W001 freezes contracts and proves migration/compatibility strategy. Independent items may inventory trust boundaries and benchmark the current authentication path if neither changes shared state.

W002 implements independent bounded owners after W001:

- I003 owns schema and migration.
- I004 owns authentication middleware against the frozen schema.
- I005 owns management API against the frozen service contract.

They share a wave only if file ownership, test fixtures, and database instances are isolated. Otherwise split them.

W003 integrates, runs migration and contract tests, verifies authorization and redaction, and measures the stated performance budget.

W004 handles operational rollout and rollback only after W003 passes.

Security criteria name denied cross-tenant access, secret-at-rest handling, log redaction, revocation, and least privilege. Performance criteria name workload and threshold. Execution evidence does not imply user acceptance.
