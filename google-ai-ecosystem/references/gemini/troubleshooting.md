# Gemini MCP Troubleshooting

Diagnose the smallest failing layer: managed runtime, Codex registration, Chrome availability, profile ownership, authentication, Gemini UI, capability, generation, or download.

## Chrome is missing

Run the installer with `--dry-run --json`. On Windows, installation occurs only when the user explicitly authorizes the mutation and the apply command includes both `--install-chrome` and `--apply`. Without that flag, absence is reported without mutation. If `winget` is unavailable or post-install detection fails, stop and direct the user to Google's official Chrome installer.

Do not substitute Edge/Brave/Chromium, install silently, import a personal profile, or make Chrome default.

## Chrome appears during normal use

Check registered `HEADLESS=true` and ensure the tool call did not request a visible browser. A visible window is appropriate only for initial login, repair, or explicitly authorized diagnosis. Background headless processes may still exist.

## Authentication required or incomplete

Do not loop the failing task. Run `get_health`, explain the visible-login flow, then use `setup_auth(show_browser=true)` when authorized. If setup fails or the window closes early, retain the recoverable profile and return `AUTH_INCOMPLETE`/the observed state.

Account switching is separate: it requires the `full` profile, an initial `re_auth(mode="switch_account")` preview, user confirmation of exact MCP-owned resources, and a second call with the receipt. Never switch because of quota/capacity.

## Profile is locked

Close MCP-owned sessions and confirm the earlier server/context exited. Do not kill unrelated Chrome processes or use the user's personal profile.

## UI selector changed

Use sanitized MCP diagnostics and update localized/semantic selectors without adding concealment, fingerprint spoofing, random human-like movement, or credential automation. Do not bypass the MCP by scripting its authenticated profile directly.

## Research or media unavailable

Separate authentication from account/service capability. Preserve the service message without hardcoded quota claims. For `MEDIA_CAPACITY`, preserve prompt/references and retry later only when the user wants to continue. For `MEDIA_TIMEOUT`, retry at most once with a larger `MEDIA_GENERATION_TIMEOUT_MS` when the original request is still useful. Do not rebuild the prompt, reauthenticate, change accounts, or start duplicate concurrent generations as an automatic workaround.

## Generated file is absent or invalid

Compare pre-submit and post-submit media candidates, allow the configured timeout, check refusal/capacity text, and save only non-empty results. Verify the absolute returned path and actual media type.

## Host cannot start the server

Verify the registered absolute Node executable/`dist/index.js`, runtime working directory, dependencies, clean build, environment, and bounded protocol smoke. If replacing a registration failed, confirm the installer restored the prior Codex configuration before changing authentication.

## Destructive tool is unavailable

`standard` deliberately hides cleanup, removal, reset, and account-switch operations. Do not call them directly. If the user explicitly requests the mutation, explain the `full` opt-in, preview the exact scope, and require the returned receipt before execution.
