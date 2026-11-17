# Code Planning Module

Apply this module to software, APIs, services, libraries, migrations, infrastructure code, and automation.

## Priority order

1. Requirement fulfillment.
2. Security.
3. Performance.
4. Consumer usability.

Higher priority wins an unavoidable trade-off. Record the trade-off rather than obscuring it.

## Planning coverage

Select only applicable concerns:

- system boundaries and architecture;
- public and internal interfaces;
- compatibility and migration;
- authentication and authorization;
- secrets, privacy, validation, and trust boundaries;
- data model, consistency, transactions, and rollback;
- concurrency, retry, idempotency, and partial failure;
- infrastructure, configuration, deployment, and rollback;
- logging, metrics, tracing, and alerting;
- test levels, fixtures, environments, and evidence;
- measurable performance budgets and baselines;
- consumer documentation and operational handoff.

Inspect the existing repository before proposing file ownership or architecture. Respect its conventions unless the request explicitly changes them.

Load [security.md](security.md) for meaningful trust boundaries or sensitive effects, [performance.md](performance.md) when latency, throughput, resource, or scale matters, and [testing.md](testing.md) for all nontrivial code plans.
