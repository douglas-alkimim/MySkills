# Google AI Ecosystem 2.0.0

This release integrates the bundled Gemini Web MCP and the Antigravity CLI workflow as one source-distributed skill.

## Highlights

- Antigravity remains the default for agentic repository engineering.
- Gemini Web MCP remains the default for research, image, and video workflows.
- Successful Gemini media is staged by the MCP, then atomically placed and verified in an authorized repository by the local agent.
- Gemini MCP authentication is manual-only: visible browser setup is available for bootstrap or repair, while normal runs remain headless.
- Automatic email/password login configuration is removed. See `vendor/gemini-mcp/docs/MIGRATION-2.0.0.md`.
- The source archive excludes dependencies, builds, caches, browser/auth state, runtimes, machine configuration, and evidence while retaining source, tests, documentation, lockfiles, license, provenance, and installers.

## Operational qualification

Release verification reports unit, smoke, package, provenance, and real-service results separately. A local build or offline smoke test does not claim authenticated Antigravity or Gemini capability; unavailable or unauthorized live checks remain `NOT_VERIFIED`.
