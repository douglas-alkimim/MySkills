# Official Antigravity Sources

Last reviewed: 2026-11-16. Use Google's current documentation for version-sensitive claims; installed `agy --help` remains authoritative for local flags.

- [Download and official installers](https://antigravity.google/download)
- [CLI installation and authentication](https://antigravity.google/docs/cli/install)
- [Headless mode and terminal JSON](https://antigravity.google/docs/cli/headless/)
- [Permissions](https://antigravity.google/docs/permissions?tab=cli)
- [CLI troubleshooting](https://antigravity.google/docs/cli/troubleshooting/)
- [Feature overview](https://antigravity.google/docs/features?tab=cli)

## Verified documentation facts

- Headless one-shot mode uses `-p` and can return one JSON object; diagnostics go to stderr.
- The JSON terminal status includes `SUCCESS`, `ERROR`, `CANCELED`, `INTERRUPTED`, `INVALID`, `WAITING`, and `RUNNING`.
- `--print-timeout` is the CLI's agent bound; it is distinct from this skill's wrapper process timeout.
- Headless approval requests can be soft-denied and still leave process exit 0, so process exit alone is insufficient.
- Permission precedence is Deny, then Ask, then Allow; broad auto-approval is inappropriate for routine delegation.
- Current models/agents are discovered through the installed CLI and account.
- Authentication may use a cached OS credential profile; first-time local sign-in can open the user's browser.

Google's docs describe stdin-capable input modes in current versions, but this skill does not claim or use that transport until the locally installed CLI and wrapper integration verify it. On the current development machine, `agy` was absent, so live transport remains `NOT_VERIFIED` and the wrapper uses constrained argv.
