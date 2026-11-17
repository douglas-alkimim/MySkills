# Antigravity Troubleshooting

Diagnose executable resolution, host access, authentication, capabilities, permissions, process lifecycle, then result parsing—in that order.

## `agy` is missing

Check explicit path, `AGY_BIN`, `PATH`, and official defaults. Run `scripts/verify_google_ai.py` or [preflight.md](preflight.md). Install only from Google's current official instructions and only when requested.

## Authentication, keyring, or network failure

First-time login is interactive. Let the user complete the official flow, then verify with `agy models`. If the sandbox blocks the OS keyring/config/network, request minimum host access. Do not change `HOME`, copy tokens, relax global permissions, or expose environment values.

## Unknown capability or model

Run `agy --help`, `agy models`, `agy agents`, and the wrapper's `--probe-transport`. Use only current identifiers and supported flags. A missing local CLI leaves transport and live execution `NOT_VERIFIED` even when documentation describes a feature.

## Tool action did not happen

Inspect the response and the existence/size of stderr diagnostics for permission denial or incomplete work. Narrow the task to read-only, use an interactive session for human approval, or configure only a specifically authorized permission. Never apply a global bypass as troubleshooting.

## Timeout

Distinguish:

- CLI/agent timeout reported in its JSON envelope;
- wrapper total timeout (`WRAPPER_TIMEOUT`, exit 4), which terminates/reaps the created tree;
- process nonzero exit (exit 4);
- valid but non-`SUCCESS` terminal status (exit 3).

Increase a bound only when the task remains useful and the previous value was genuinely insufficient. Do not repeatedly restart the same hung task.

## Invalid or ambiguous output

The wrapper rejects missing/wrongly typed fields and more than one parseable JSON object. It never prints `--response-only` before terminal validation. Capture direct CLI stdout/stderr separately; do not strip diagnostics into an apparently successful answer.

## Update failure

An update mutates the installation and may fail on a locked/read-only binary. Report the current version and request authorization before changing it. Do not update as an implicit fix.

