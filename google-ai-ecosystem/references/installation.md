# Installation, Update, and Rollback

Installation mutates the host. Start with a read-only preflight and dry-run; use `--apply`, registration replacement, or browser installation only when the user requested or approved that exact change.

## Preflight

From the skill directory, run:

```text
python scripts/verify_google_ai.py
```

This inspects Python, Node, pnpm, `agy`, Chrome, bundled Gemini source, and available Codex registration without installing software or opening an authenticated browser.

## Antigravity CLI

The skill does not bundle `agy`. For a current installation, read [antigravity/official-docs.md](antigravity/official-docs.md) and use Google's official installer for the operating system. Do not use an unofficial package or copied binary.

After installation:

```text
agy --version
agy --help
agy models
agy agents
```

First-time sign-in may require an interactive `agy` session and the user's browser. Never copy the credential store or place an API key in this skill, a prompt, or a log.

## Gemini MCP dry-run

The vendored source is under `vendor/gemini-mcp`. The installer creates a versioned runtime; it does not put browser state in the skill or project.

Plan a Codex project registration:

```text
python scripts/install_gemini_mcp.py --host codex --scope project --project-root <project> --register --dry-run --json
```

Apply a first installation and registration:

```text
python scripts/install_gemini_mcp.py --host codex --scope project --project-root <project> --register --apply --json
```

If a registration with the same server name already exists, leave it untouched unless replacement is explicitly intended. For an approved replacement:

```text
python scripts/install_gemini_mcp.py --host codex --scope project --project-root <project> --register --replace-registration --apply --json
```

Registration is transactional: the installer snapshots the Codex configuration, adds and verifies the candidate, and restores the exact previous configuration on failure.

## Chrome consent

The installer first detects supported Google Chrome paths. Existing Chrome is never reinstalled, replaced, downgraded, made default, or given the user's everyday profile.

If Chrome is absent on Windows, dry-run/application without consent reports the missing prerequisite. Add `--install-chrome` only after explicit consent:

```text
python scripts/install_gemini_mcp.py <other-options> --install-chrome --apply
```

That path uses the exact stable `Google.Chrome` package through noninteractive `winget` and then re-detects the executable. `--skip-chrome-install` records that no browser installation may occur. Do not combine the two flags. On macOS/Linux, the installer reports the prerequisite instead of inventing an unverified package command.

## Build verification

The managed build uses the lockfile and runs install, clean build, unit tests, and bounded MCP smoke before registration. In the vendored source, the corresponding checks are:

```text
pnpm install --frozen-lockfile
pnpm test
pnpm run build
pnpm run smoke
pnpm run package:check
pnpm run license:check
pnpm run provenance:check
```

Passing these commands proves local packaging/protocol behavior, not an authenticated Gemini capability.

## Profiles and explicit full opt-in

Missing, unreadable, invalid, or reset settings use the restricted `standard` profile. To inspect or deliberately change a managed runtime:

```text
node <runtime>/dist/index.js config get
node <runtime>/dist/index.js config set profile full
node <runtime>/dist/index.js config reset
```

`config reset` returns to `standard`. `full` enables destructive tools and is an explicit opt-in; direct calls to tools outside the active profile are denied before the handler runs.

## Authentication and rollback

Installation never opens a login window. After registration, call `get_health`. If authentication is absent or expired, follow [gemini/authentication.md](gemini/authentication.md); normal use remains hidden and only the MCP-owned profile is allowed.

For rollback, restore the prior registration/config snapshot or register the previous versioned runtime. Do not delete the MCP browser profile while rolling back code. A failed replacement is expected to restore the prior Codex configuration automatically.

