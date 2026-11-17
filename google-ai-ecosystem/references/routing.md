# Canonical Routing

Choose one primary route from the user's intended outcome. A secondary route is a fallback or an explicit second phase, not an automatic parallel invocation.

## Decision tree

1. If the user explicitly chooses Antigravity or Gemini, honor that choice when the requested capability exists and the route is safe. Explain any capability or authorization blocker instead of silently substituting.
2. If the task changes, investigates, or verifies a software repository, use Antigravity.
3. If the task creates or edits an image/video, or requires Gemini Web research/knowledge capabilities, use Gemini.
4. If both are materially needed, define a serial handoff artifact. Otherwise keep one route.
5. If neither external component adds value, use local tools.

## Eight routing categories

| Category | Primary | Secondary | Conditions and exceptions | Delegation and handoff | Fallback |
|---|---|---|---|---|---|
| 1. Software engineering and repository operations | Antigravity | Local agent; Gemini bridge only by explicit request | Includes exploration, architecture, planning, implementation, debugging, refactoring, tests, review, and technical investigation of project files. | Give Antigravity an exact workspace/scope; it may return findings or edit only authorized paths. Local agent reviews diff and reruns checks. | If `agy` is unavailable, continue locally or offer installation; do not silently route ordinary implementation to Gemini. |
| 2. Multi-agent development and delegation | Antigravity | Local subagents when separately available/authorized | Use only when independent workstreams, specialist review, or meaningful parallelism justify coordination. | Define non-overlapping ownership or isolated worktrees and an integration owner. | Collapse to one agent when work is coupled, small, or shared-write risk is high. |
| 3. Image generation and image workflows | Gemini MCP | Local image tooling only when the user chooses it | Use `create_image` with a master media contract and only authorized references. | Local agent verifies staging, places it in the explicit or inferred authorized repository destination, and reports a relative path/hash. | If the capability is unavailable, report `NOT_VERIFIED`/service error and offer a later retry or user-approved alternative. |
| 4. Video generation and video workflows | Gemini MCP | User-approved alternative media tool | Use `create_video`; availability, model, duration, and quota are observed at runtime, never assumed. | Local agent validates the container, atomically places it in the explicit or inferred authorized repository destination, and reports a relative path/hash. | Preserve prompt/references and report capacity/refusal; do not switch accounts or loop identical requests. |
| 5. Deep research and knowledge investigation | Gemini MCP | Antigravity for repository-grounded technical investigation | Use Gemini `deep_research` for Web synthesis or knowledge work not centered on modifying a repository. | Return research with sources/uncertainty; if implementation follows, hand off a bounded findings/specification artifact to Antigravity. | Use ordinary Gemini chat or local primary-source research when deep research is unavailable. |
| 6. General conversation and research | Gemini MCP when Gemini Web adds value | Local agent | Use for complex conversational queries, Web-oriented knowledge, or explicit Gemini conversation. Do not externalize routine questions unnecessarily. | Usually one Gemini session; local agent validates current/high-stakes claims. | Answer locally when sufficient or when Gemini authentication/capability is unavailable. |
| 7. Hybrid workflow | Tool owning the first necessary phase | The other tool in a named second phase | Use both only when outputs cross domains, such as research→implementation or repository→visual asset. | Name the artifact and direction: e.g. Gemini research brief → Antigravity implementation; Antigravity product spec → Gemini image/video prompt. Run phases serially unless independence is proven. | Complete the viable phase, state the missing handoff, and never present partial work as end-to-end success. |
| 8. Explicit user tool preference | User-selected tool | Default route only after explanation/consent | Preference wins unless the tool lacks the capability, would violate authorization, or the requested action is unsafe. | Keep the chosen tool's normal verification and permission boundaries. | Explain the blocker and offer the default route; do not substitute silently. |

## Gemini agentic bridge

Gemini Web chat is not a local repository agent by default. Use its bridge only when the user explicitly asks Gemini to draft/analyze the task or when browser-grounded research is integral. The handoff must be a complete file body, patch, structured artifact, or bounded plan. The local agent applies writes, inspects the diff, and tests.

## Hybrid examples

- “Research the current protocol and implement it here”: Gemini produces a source-backed requirements brief; Antigravity implements against named files; the local agent verifies both handoff and code.
- “Inspect this app and create a launch visual”: Antigravity produces a concise visual/product specification from the repository; Gemini creates the asset from that specification and authorized references.
- “Use Gemini to propose this refactor”: honor Gemini explicitly through the task bridge; the local agent applies/verifies, or Antigravity may implement only if the user accepts that second phase.

Do not describe browser automation as an official Gemini API, do not use Antigravity for Gemini-only media generation, and do not invoke both tools merely because both are installed.
