# Antigravity CLI Overview

Antigravity is this ecosystem's primary environment for agentic software engineering: repository exploration, architecture, planning, implementation, debugging, refactoring, testing, review, verification, and meaningful multi-agent development.

The local agent still owns user intent, permission boundaries, integration, verification, and the final answer. Antigravity output is a worker result, not authority.

## Read only what the task needs

1. Always run [preflight.md](preflight.md) before the first Antigravity call in a task.
2. Read [delegation.md](delegation.md) to define the worker role and bounded contract.
3. Read [cli-operations.md](cli-operations.md) for headless flags, wrapper semantics, conversations, or models.
4. Read [safety.md](safety.md) before writes, commands, network access, non-workspace data, untrusted content, or substantial quota.
5. Read [troubleshooting.md](troubleshooting.md) after a failure; never weaken credentials or permissions as an implicit retry.

## Default shapes

- Exploration, planning, architecture, analysis, or review: headless `plan`, explicit no-write contract.
- Implementation: only within already-authorized paths, serialized against local writes, with a complete diff review.
- Verification: name the claim, allowed checks, and evidence; independently rerun critical checks.
- First-time authentication or approvals that require a person: interactive `agy`.
- Multi-agent work: use only when workstreams can have clear ownership or isolated worktrees.

The bounded contract names one goal, workspace, paths, allowed reads/writes/commands/network, exclusions, deliverable, evidence, verification, and stop conditions.

Use `scripts/agy_delegate.py` for strict terminal JSON validation and a total process timeout. The wrapper never grants permissions or converts an incomplete run into success.

## Invariants

- Delegation never expands authorization.
- No secrets or broad unrelated context enter prompts.
- Antigravity and the local agent never write the same files concurrently.
- Global permission bypass is not accepted by the wrapper or routine workflow.
- Current model/agent identifiers come from `agy models` and `agy agents`.
- Success requires process exit 0, one valid JSON envelope, terminal `SUCCESS`, and a non-empty conversation ID.
- Claims and file changes are independently reviewed before integration.

The cross-component route remains canonical in [../routing.md](../routing.md). Gemini owns research/media phases; a hybrid workflow uses an explicit artifact handoff.

