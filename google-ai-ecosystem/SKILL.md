---
name: google-ai-ecosystem
description: Route and operate Google Antigravity CLI for agentic software engineering or the bundled Gemini Web MCP for research, deep research, image, and video workflows. Use for Antigravity/Gemini setup, repository delegation, Gemini media, and an explicitly requested Gemini Web task bridge; Antigravity is the default for repository work and Gemini is the default for research and media.
---

# Google AI Ecosystem

Choose one primary route. Antigravity is the agentic development environment for repositories; Gemini Web is the research and media environment. Gemini can draft a coding artifact through an explicit task bridge, but it is not the default local coding agent.

## Choose the route

Respect an explicit user choice when the route is supported and safe. Otherwise:

- Repository exploration, architecture, planning, implementation, debugging, refactoring, testing, review, or meaningful multi-agent development → **Antigravity CLI**.
- Deep research, Web knowledge investigation, complex non-repository conversation, image work, or video work → **Gemini Web MCP**.
- A task needing both → name the two phases, the handoff artifact, and which tool owns each phase; do not invoke both automatically.
- Routine work that the local agent can complete directly → use local tools; delegation must add decision value.

Read [references/routing.md](references/routing.md) when the route or handoff is not obvious. It is the canonical routing matrix.

## Operate the selected component

- Before an Antigravity call, read [references/antigravity/overview.md](references/antigravity/overview.md). Use a bounded contract and independently review its result.
- For Gemini research or normal MCP operations, read [references/gemini/mcp-operations.md](references/gemini/mcp-operations.md).
- For Gemini image/video generation, read [references/gemini/media-generation.md](references/gemini/media-generation.md) and preserve the user's prompt plus authorized reference images.
- Use the [explicit Gemini task bridge](references/gemini/agentic-bridge.md) only when the user asks for Gemini Web to draft or perform the reasoning phase. Gemini returns a proposal; the local agent writes files and verifies the result.
- For installation, updates, or recovery, read [references/installation.md](references/installation.md) plus the component-specific reference it links.

## Preserve boundaries

- Delegation never expands authorization, filesystem scope, network scope, or permission to make external changes.
- Never send credentials, cookies, tokens, browser state, `.env` contents, unrelated private files, or unnecessarily broad context.
- Do not let Antigravity and the local agent write the same mutable files concurrently.
- Treat external output as unverified until checked against the workspace, primary sources, diffs, builds, tests, or media inspection.
- Gemini Web automation is browser automation through a dedicated MCP profile, not an official Gemini API.

## Gemini browser and authentication

Normal Gemini work is headless/hidden and uses only the MCP-owned Chrome profile. A visible Chrome window is allowed for initial login, non-destructive authentication repair, or explicit diagnosis.

On `AUTH_REQUIRED`, inspect `get_health`; do not loop the task or silently switch accounts. Explain the visible-login step, call `setup_auth(show_browser=true)` when authorized, let the user finish Google login, then retry the original call. Account switching is a distinct receipt-confirmed operation. Read [references/gemini/authentication.md](references/gemini/authentication.md).

## Bundled helpers

- `scripts/install_gemini_mcp.py`: dry-run-first, versioned Gemini MCP installation and optional transactional Codex registration.
- `scripts/agy_delegate.py`: bounded Antigravity process wrapper with strict JSON terminal validation.
- `scripts/build_gemini_prompt.py`: deterministic task-bridge and media prompt builder.
- `scripts/verify_google_ai.py`: read-only environment preflight.

Persistent host changes require the user's request or approval. Live media and research availability is account/service dependent; report `REAL`, `SMOKE`, or `NOT_VERIFIED` honestly rather than inferring capability from unit tests.

After every successful Gemini image or video generation, place each returned staging file in a useful authorized repository/workspace location with `scripts/place_media.py`. An explicit user destination wins; otherwise use an existing media convention or `artifacts/media/images/` / `artifacts/media/videos/`. Report the repository-relative path and integrity metadata. Never delete staging, add the file to Git, or choose silently between multiple plausible roots.
