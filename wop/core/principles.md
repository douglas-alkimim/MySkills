# WOP Principles

These principles govern every plan, prompt, lifecycle operation, and specialist module.

| ID | Principle | Operational rule |
|---|---|---|
| P01 | Self-containment | Put execution-critical facts, contracts, and criteria in the plan and relevant wave prompt. |
| P02 | Precision | Replace material unstated assumptions with facts, decisions, declared assumptions, or unknowns. |
| P03 | Sequentiality | Treat waves as a strictly ordered chain with a hard barrier after each wave. |
| P04 | Independence | Co-locate items only when they have no prerequisite or interference relationship. |
| P05 | Parallelism | Maximize useful safe concurrency, not item or agent count. |
| P06 | Verifiability | Give every item and wave measurable acceptance criteria and evidence requirements. |
| P07 | Traceability | Map every material requirement to work, outputs, and verification. |
| P08 | Adaptability | Match planning depth to risk, uncertainty, dependencies, and coordination cost. |
| P09 | Transparency | Label facts, decisions, assumptions, unknowns, and evidence distinctly. |
| P10 | Modularity | Load specialist guidance only when the task needs it. |
| P11 | Agent-oriented writing | Use actionable, dense instructions with explicit boundaries and completion conditions. |
| P12 | Governance | Control revisions, blockers, failures, acceptance, and destructive actions. |
| P13 | Persistence | Store plans as durable packages with stable IDs and indexed lifecycle history. |
| P14 | Integrity | Keep README, prompts, paths, versions, hashes, relations, and SQLite records consistent. |

When principles compete, preserve safety, correctness, explicit user intent, and authorization. Parallelism never overrides independence; brevity never overrides execution-critical completeness.

WOP optimizes useful independent work, not the number of waves, items, or agents. One wave with one item is complete when it expresses the real work. Split only when the split creates independent execution, improves verification, or reduces risk enough to justify coordination overhead.
