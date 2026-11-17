# Example: Multi-Agent Execution

Wave W002 contains three independent items after W001 freezes an interface:

| Item | Owner | Exclusive scope | Output |
|---|---|---|---|
| I004 | Agent A | src/client/ | client implementation |
| I005 | Agent B | src/server/ | server implementation |
| I006 | Agent C | tests/contract/ | contract test suite |

The frozen interface is included in every dispatch prompt. Agents use isolated worktrees and must not edit the interface file. Test fixtures use separate namespaces.

The orchestrator dispatches all three, waits for all reports, and verifies item evidence. A failed I006 blocks W003 even if I004 and I005 pass. The orchestrator integrates outputs, runs the contract suite against both implementations, records results, and evaluates the W002 gate. Only then may W003 start.

An agent that discovers a contract defect stops affected work and proposes a plan revision. It does not repair the shared contract silently.
