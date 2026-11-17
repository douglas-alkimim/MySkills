# Gemini MCP runtime contracts

Status: implemented contract for the bundled Google AI Ecosystem runtime.

## Authorization (GC002-GC003)

- A single authorization decision owns both tool discovery and tool invocation.
- A missing, unreadable, malformed, unknown-profile, or invalid settings file resolves to the explicit `standard` safe profile plus an actionable diagnostic. It never resolves to `full`.
- `standard` is an explicit allowlist. `full` is only selected by a valid, explicit user setting or environment override.
- `disabledTools` can only reduce access. Unknown tool names and malformed values fail validation; they never widen access.
- A direct call to a hidden or disabled tool returns a structured `TOOL_NOT_AUTHORIZED` error before handler lookup or side effects.

## Destructive confirmation (GC004)

- Preview returns an opaque, single-use receipt containing the operation, canonical resources, resource state/version, scope hash, issue/expiry timestamps, and a nonce.
- Execution requires that exact receipt. Operation, canonical target, state, version, hash, expiry, or prior consumption mismatch invalidates it.
- Canonical paths must be descendants of an MCP-owned root after realpath resolution. Prefix-string checks are prohibited.
- The receipt is consumed atomically immediately before mutation. A failed mutation is reported precisely and does not authorize a retry with the same receipt.

## Authentication state (GC005)

Valid states are `unconfigured`, `valid`, `repairable`, `expired`, `switch_requested`, and `failed_recoverable`.

- Initial setup creates a candidate profile and only promotes it after successful validation.
- Repair preserves the current profile and a recoverable snapshot until the candidate is validated.
- Account switch is explicit, separate, and destructive only after operation-bound confirmation.
- Cleanup never doubles as setup, repair, or account switch.
- Partial failure keeps the last recoverable state and reports the next safe action; it does not silently clear the active profile.

## Sensitive data and logs (GC006)

- User prompt/response content, cookies, tokens, profile contents, attachment contents, and full user paths are absent from logs by default.
- Redaction happens before every sink and handles nested objects, exceptions, URLs, headers, and environment-derived values.
- State/session writes are atomic and use restrictive permissions or ACLs. Failure to establish the required protection fails closed with a diagnostic.
- Test fixtures are synthetic. Evidence stores commands, versions, hashes, classifications, and sanitized summaries only.

## Browser behavior (GC007)

- Normal execution is hidden/headless; login can be made visible by explicit setup or repair flow.
- Automation is transparent and deterministic. No anti-detection flags, fabricated fingerprint, human-error typing, mouse simulation, or random jitter is allowed.
- Locale and timezone are validated explicit settings or derived from the host environment; no unrelated fixed geography is imposed.

## Tests and evidence (GC008, GC012)

- `pnpm test` runs finite offline unit tests and exits. `pnpm run smoke` is separate and bounded.
- Evidence classifications are `UNIT`, `MOCK`, `SMOKE`, `REAL`, and `NOT_VERIFIED`.
- A mock or smoke never proves a real service capability. An unavailable or unauthorized real capability remains `NOT_VERIFIED`.

## Version and provenance (GC009)

- `package.json` is the canonical runtime version source.
- Release metadata must record upstream repository, immutable commit, vendored tree hash, vendoring date, and local patch summary.
- Build and package checks use the committed lockfile; version banners and server metadata read the canonical version rather than duplicating literals.

## Routing and compatibility (GC001, GC010-GC011)

- Antigravity is the default for repository engineering and multi-agent execution.
- Gemini is the default for research, deep research, image, and video. Gemini agentic bridging is secondary and only used when explicitly requested.
- Hybrid work has an explicit artifact handoff and never invokes both systems implicitly.
- Antigravity success requires a valid envelope, acceptable process exit, and terminal status `SUCCESS`; wrapper timeout and CLI timeout remain distinct.
- Login visibility on demand, normal hidden execution, reference attachments, media downloads, Chrome detection, and consented installation are compatibility requirements.
