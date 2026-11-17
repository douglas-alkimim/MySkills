# Gemini MCP Authentication

Gemini Web authentication is manual, recoverable, and restricted to the MCP-owned Chrome profile. Normal calls are headless/hidden; a visible window is a login/recovery UI, not a concealment mechanism.

Automatic email/password authentication is not supported. New registrations contain no credential-auth setting. If an old registration still contains credential fields or an enabled legacy flag, startup fails before a browser opens with `LEGACY_AUTO_LOGIN_UNSUPPORTED`; remove those fields, restart the MCP, and use the visible setup flow below. An old disabled flag is inert only long enough for transactional registration migration and is not copied to the replacement.

## State model

| State | Meaning | Safe next action |
|---|---|---|
| `unconfigured` | No saved MCP state exists | Run visible `setup_auth` when the user is ready to sign in. |
| `valid` | Persisted critical cookies are present and not expired | Continue normally; `setup_auth` is a no-op that preserves the profile. |
| `repairable` | State exists but is malformed or lacks required cookie evidence | Use visible `setup_auth`; or opt into `full` and use `re_auth(mode="repair")` when its explicit recovery contract is needed. |
| `expired` | A critical persisted cookie has expired | Use visible setup/repair; do not delete or switch accounts automatically. |
| `switch_requested` | An account-switch preview receipt is live | Await explicit confirmation or let it expire; no data is cleared by preview. |
| `failed_recoverable` | A login/switch attempt failed and the recovery snapshot was restored | Inspect health, then retry repair when the user is ready; do not clean up first. |

Runtime navigation may still discover that apparently valid persisted state no longer authenticates. Treat that as `AUTH_REQUIRED` and recover; do not make a destructive decision from file inspection alone.

## Initial login or non-destructive repair

1. Call `get_health` and inspect `auth_status` and `browser_visible`.
2. Explain that a temporary Chrome window owned by the MCP is required.
3. With the user's authorization, call `setup_auth` with `show_browser=true`.
4. The user signs in and waits for `gemini.google.com/app` to load.
5. The MCP atomically saves state/session data and closes its context when complete.
6. Call `get_health` again, then retry the original task. Normal execution returns to headless mode.

Closing early or failing to authenticate returns `AUTH_INCOMPLETE`; the prior recoverable snapshot is retained. Never delete the profile merely because login failed or a token expired.

Suggested wording:

> The Gemini MCP session needs login or repair. I can open the Chrome profile owned by the MCP so you can sign in. After Gemini loads, return here and retry; normal calls will be hidden again.

## Explicit account switch

Account switching is not a quota workaround and is never automatic. It is available only in the explicit `full` profile:

1. Call `re_auth` with `mode="switch_account"` and no receipt.
2. Show the returned MCP-owned state/session/profile resources to the user.
3. Only after confirmation, call again with the same mode and receipt.
4. The MCP snapshots the current data, clears only the reviewed resources, opens login, and rolls back on failure.

Receipts are short-lived, state-bound, and single use. A changed resource, expired receipt, or replay is denied.

## Browser invariants

- Only the dedicated MCP profile may be used; never inspect or automate the user's personal Chrome profile.
- Normal tasks must not request `show_browser`.
- Only one MCP process may own the persistent profile at a time.
- A background headless process may exist, but no normal Chrome window/taskbar UI is expected.
- Closing the MCP server must close its browser context and release profile locks.
- Never include cookies, session storage, tokens, or user prompts in evidence.
- Never place an email, password, API key, or browser state in MCP environment configuration.

