# Migration to 2.0.0

Version 2.0.0 removes automatic sign-in with account credentials. This is a breaking configuration change: a legacy enabled flag or either legacy credential field now stops startup before Chrome opens and returns `LEGACY_AUTO_LOGIN_UNSUPPORTED`. Values are never read into logs or error messages.

## Safe migration

1. Preserve the existing MCP-owned browser profile and session data.
2. Replace the MCP registration transactionally with the 2.0.0 entrypoint.
3. Remove all legacy credential-authentication keys from the registration. Do not copy their values elsewhere.
4. Restart the MCP and call `get_health`.
5. If health reports an unconfigured, expired, or repairable session, call `setup_auth(show_browser=true)`, let the user complete Google sign-in, close the visible browser after success, and retry the original operation.

Normal operation remains headless. Explicit account switching still requires preview and confirmation; migration must not clear or switch the current account.

## Rollback

Rollback changes only the MCP entrypoint/registration to the last accepted release. Do not delete the browser profile, session data, staging media, or prior managed release. A rollback restores runtime compatibility but does not re-enable credential automation.
