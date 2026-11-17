# Plan Integrity Audit

Mandatory at every planning level. Depth never permits unchecked filesystem, prompt, identity, or SQLite state to pass. A concise success summary is sufficient for a simple plan; list evidence for every conflict or failure.

- [ ] Package name matches the naming convention.
- [ ] README metadata is complete and valid.
- [ ] Stable ID is not tombstoned.
- [ ] SQLite-authoritative operational states agree with the README projection; conflicts are reported, not overwritten.
- [ ] Version and language agree across README and prompts.
- [ ] Wave prompt count exactly equals wave count.
- [ ] No extra or placeholder wave prompt exists.
- [ ] Every prompt source hash matches README.
- [ ] Later prompts name and verify predecessor gates.
- [ ] Later prompts name predecessor producer items, outputs, evidence, criteria, and handoff contracts.
- [ ] The global protocol contains only rules applicable to every wave and no item-specific assignment.
- [ ] Every prompt's authorized-item metadata and assigned-item markers exactly match its wave.
- [ ] Wave execution instructions do not reference foreign items or authorize later waves.
- [ ] Prerequisites appear once, under predecessor verification, rather than being duplicated in execution scope.
- [ ] Custom global sections reach every wave prompt and execute-all.
- [ ] Custom wave/item sections reach only their selected wave prompts; every selector resolves.
- [ ] Unscoped custom sections propagate globally, so no custom context disappears silently.
- [ ] execute-all references every prompt once and in order.
- [ ] Every referenced relative path exists.
- [ ] SQLite ID, path, directory, metadata, hash, and archive state agree.
- [ ] Relationships reference existing, appropriate plans.
- [ ] The `depends_on` graph is acyclic; associative relations are not misclassified as dependencies.
- [ ] No integrity result is `unchecked`, `missing`, `invalid`, or `conflict`.
- [ ] No operation remains `pending` or `failed`, and no staged deletion or prompt directory remains.
- [ ] Mechanical validation passed.
- [ ] Semantic consistency review passed.
