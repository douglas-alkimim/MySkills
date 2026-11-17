# Dependency Analysis

Model both prerequisite and interference edges.

## Edge types

- Output: B consumes an artifact produced by A.
- Decision: B depends on a choice resolved by A.
- Contract: B implements or tests an interface frozen by A.
- File-edit: A and B may change the same file, region, or generated output.
- Shared-resource: both mutate one database, service, environment, account, lock, or quota.
- Integration: B can be evaluated only after A is integrated.
- External: availability, approval, procurement, deployment window, or third-party response.

An edge places items in different waves unless execution isolation removes the interference and the plan states how. Separate branches, isolated fixtures, or independent database schemas may prove isolation; optimistic assertions do not.

## Analysis procedure

1. List each item’s inputs, outputs, decisions, writes, and external effects.
2. Compare every candidate same-wave pair.
3. Direct prerequisite edges from producer to consumer.
4. Treat symmetric interference as an ordering decision and document the chosen direction.
5. Detect cycles. Break them by freezing a contract, creating a discovery/prototype item, narrowing ownership, or merging inseparable items.
6. Topologically layer the acyclic graph.
7. Recheck hidden coupling introduced by integration and verification.

Unknown dependency facts become a discovery item in an earlier wave or a clarification blocker. Never schedule around an unknown by assuming independence.
