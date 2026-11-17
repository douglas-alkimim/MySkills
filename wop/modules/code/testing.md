# Code Testing Module

Map risks and requirements to the cheapest reliable test level.

- Unit tests isolate pure contracts and edge cases.
- Integration tests cover boundaries such as databases, files, queues, and external adapters.
- Contract tests protect producer-consumer interfaces.
- End-to-end tests cover critical user or operational journeys.
- Static checks cover syntax, types, lint, policy, and schema invariants.
- Property, fuzz, concurrency, migration, security, and performance tests apply when their risks exist.

Specify fixtures, isolation, deterministic clocks or randomness, environment, commands, and expected evidence. Test failure paths, retry/idempotency, permissions, compatibility, and rollback where applicable.

Avoid tests that merely assert generated wording or implementation details without protecting behavior. A plan is not ready when critical acceptance depends on a test environment that has no owner or provisioning step.
