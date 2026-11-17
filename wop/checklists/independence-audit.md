# Independence Audit

A one-item wave requires no pairwise report. Confirm only that the item does not depend on unreleased work. When multiple items coexist, compare every pair:

- [ ] Neither consumes the other’s output.
- [ ] Neither waits for the other’s decision.
- [ ] Neither changes the other’s contract.
- [ ] File and artifact ownership do not overlap.
- [ ] Shared mutable resources are absent or genuinely isolated.
- [ ] External effects can occur concurrently without conflict.
- [ ] Tests and fixtures are isolated.
- [ ] Integration does not require mid-wave coordination.
- [ ] Each item can pass or fail independently.
- [ ] The parallelism rationale states the evidence.

For Extensive plans, also document the isolation mechanism, failure containment, integration order, and coordination overhead. If any applicable box cannot be supported, separate the items, merge inseparable fragments, or create explicit isolation first. Do not split merely to increase item or agent count.
