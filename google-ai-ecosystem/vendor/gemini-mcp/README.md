# Google AI Ecosystem — Gemini Web MCP runtime

This is the private MCP runtime bundled with the Google AI Ecosystem skill. It supports browser-based Gemini research and media workflows with recoverable manual authentication, bounded session handling, and an MCP-owned browser profile.

It is not intended for independent npm publication. Install and register it through the parent skill's `scripts/install_gemini_mcp.py` workflow, which builds a versioned runtime from the lockfile and keeps browser state outside the source tree.

## Local verification

From this directory, use Node.js 18 or newer and pnpm:

```text
pnpm install --frozen-lockfile
pnpm test
pnpm run build
pnpm run smoke
pnpm run package:check
pnpm run license:check
pnpm run provenance:check
```

The real-service smoke test is separate because it requires an authorized Gemini session. Offline tests and lifecycle smoke checks do not claim that an authenticated service capability was exercised.

## License and provenance

This component contains modified third-party MIT-licensed code. The included [`LICENSE`](LICENSE) preserves the original copyright and permission notice. [`VENDOR.json`](VENDOR.json) records the source, immutable upstream reference, vendoring date, tree hash, and local changes needed for compliance and reproducibility.
