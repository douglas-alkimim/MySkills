# Gemini MCP Operations

The bundled server transparently automates Gemini Web through a dedicated persistent Chrome profile. It is not an official Gemini API; selectors and account-visible capabilities can change.

## Normal environment

```text
HEADLESS=true
CONVERSATION_URL=https://gemini.google.com/app
MEDIA_GENERATION_TIMEOUT_MS=720000
RESEARCH_TIMEOUT_MS=900000
```

Generated media is written under `GEMINI_OUTPUT_DIR`. Locale/timezone use validated explicit environment values when supplied, otherwise the local environment; no fabricated fingerprint or human-like interaction is used.

Credential-based login configuration was removed. A legacy enabled flag or credential field produces `LEGACY_AUTO_LOGIN_UNSUPPORTED` before browser launch and never logs its value. Replace the old registration transactionally, then use `setup_auth(show_browser=true)` for initial login or repair.

## Profiles

The fail-closed `standard` profile exposes exactly:

- `ask_question`, `select_model`, `use_gemini_tool`;
- `list_conversations`, `get_conversation`, `select_conversation`, `search_conversations`, `get_library_stats`;
- `list_sessions`, `close_session`;
- `get_health`, `setup_auth`.

`minimal` is smaller. `full` is explicit opt-in and additionally exposes mutations such as add/update/remove conversation, session reset, account switch/repair through `re_auth`, and cleanup. Tool discovery and direct calls use the same guard; an unavailable tool returns `TOOL_NOT_AUTHORIZED` before side effects.

## Primary operations

- `get_health`: actual auth state, browser visibility, and session statistics.
- `setup_auth`: visible initial login or non-destructive setup; preserves a valid profile.
- `ask_question`: normal Gemini Web conversation.
- `select_model`: choose among runtime-detected UI modes exposed by the server.
- `use_gemini_tool`: `deep_research`, `create_image`, or `create_video`.
- `re_auth` (`full`): non-destructive repair or receipt-confirmed account switch.
- `cleanup_data` (`full`): preview then receipt-confirmed deletion of MCP-owned roots only.
- `remove_conversation` (`full`): preview then state-bound receipt-confirmed removal.

## Destructive operations

Never treat a text confirmation as execution authority. First call the operation without a receipt, present the exact preview, and execute only with the same unexpired receipt after user confirmation. Any operation, resource, state, scope, or TTL mismatch is denied. Cleanup never scans npm, editors, other AI tools, personal Chrome, general caches, or Trash.

## Failure handling

- `AUTH_REQUIRED`: stop retrying, inspect health, and offer the visible login flow.
- `AUTH_INCOMPLETE`: login was cancelled or did not reach an authenticated Gemini page; previous recoverable data remains.
- `QUOTA_OR_CAPACITY_OBSERVED`: report only the observed service message and retryability; do not invent reset dates/limits or recommend account switching.
- `MEDIA_CAPACITY`: authentication/transport may still be healthy; preserve prompt/attachments and retry later only when useful.
- `MEDIA_TIMEOUT`: Gemini did not expose a ready media result before the configured deadline. Retry at most once with a larger `MEDIA_GENERATION_TIMEOUT_MS`; do not switch accounts or start duplicate concurrent generations.
- `TOOL_NOT_AUTHORIZED`: inspect the active profile; do not bypass the dispatcher.
- profile lock: close the prior MCP-owned session/context; never kill unrelated Chrome processes.

Read [authentication.md](authentication.md), [media-generation.md](media-generation.md), and [troubleshooting.md](troubleshooting.md) only for the relevant operation.
