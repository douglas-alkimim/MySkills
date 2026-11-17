# Antigravity Preflight

Use this read-only check before the first call in a task.

## 1. Resolve the executable

Resolution order in the bundled wrapper is:

1. explicit `--agy-bin`;
2. `AGY_BIN`;
3. `agy`/`agy.exe` on `PATH`;
4. official default locations: `~/.local/bin/agy` and `%LOCALAPPDATA%\agy\bin\agy.exe` (plus the real user-profile candidate on sandboxed Windows).

Check without installing:

```powershell
Get-Command agy -ErrorAction SilentlyContinue
agy --version
```

If missing, report it. Installation is a host mutation and follows [../installation.md](../installation.md) only when requested.

## 2. Probe current capabilities

```text
agy --version
agy --help
agy models
agy agents
python scripts/agy_delegate.py --cwd <workspace> --probe-transport
```

The transport probe calls only local `agy --help`; it sends no prompt. Do not claim a model, agent, stdin/file transport, sandbox, or permission behavior that the installed CLI did not expose.

## 3. Verify authentication

Headless mode uses cached credentials. If they are absent, run `agy` interactively and let the user complete the official sign-in flow. Google also documents an API-key provider route, but a key is never printed, copied, persisted by this skill, or included in a worker prompt.

If the host sandbox blocks the OS keyring, config directory, or network, request only the minimum external access required. Do not change `HOME`, copy credential stores, or weaken keyring permissions.

## 4. Establish workspace and scope

Resolve the intended `--cwd`, inspect repository instructions such as `AGENTS.md`/`GEMINI.md`, and pass only material constraints. Add another directory only when it is authorized and necessary.

For analysis, use `plan` and no writes. For implementation, name exact write paths and verification. Do not assume a terminal sandbox exists merely because a flag is documented; confirm runtime support.

## 5. Bound time and cost

Choose a current model/effort proportional to the task, set both CLI and wrapper timeouts, and avoid duplicate calls. Substantial/repeated use should remain visible to the user.

