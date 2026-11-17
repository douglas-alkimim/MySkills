# Antigravity CLI Operations

The installed `agy --help` is authoritative for that machine. Google's headless interface uses `-p`, JSON output, and `--print-timeout`:

```text
agy -p "<bounded prompt>" --mode plan --output-format json --print-timeout 15m
```

Discover models/agents at runtime:

```text
agy models
agy agents
```

Pin one only when reproducibility or the task benefits. Unknown pinned models must fail rather than silently fall back.

## Bundled wrapper

```text
python <skill-dir>/scripts/agy_delegate.py \
  --cwd <workspace> \
  --mode plan \
  --prompt-file <prompt.txt> \
  --print-timeout 15m \
  --wrapper-timeout-seconds 1200
```

`--prompt-file -` reads the wrapper input from stdin, but the current wrapper still passes the resulting prompt to `agy -p` as process argv. This does **not** make the CLI transport secret-safe. Until a locally installed CLI proves and passes integration tests for another transport:

- maximum prompt length is 12,000 characters;
- apparent credentials/private keys are rejected before process creation;
- do not put sensitive content in any prompt source;
- the local capability probe reports argv honestly.

The wrapper forces JSON, validates exactly one terminal object, requires typed `status`/`response`, and requires a non-empty `conversation_id` on `SUCCESS`. `--response-only` is emitted only after all validation.

## Timeouts and exit classes

- `--print-timeout`: Antigravity's own agent timeout.
- `--wrapper-timeout-seconds`: total subprocess wall-clock limit (default 1200 seconds).
- `--terminate-grace-seconds`: grace between tree terminate and forced kill.

Wrapper exit meanings:

- `0`: process exit 0 and validated terminal `SUCCESS`;
- `2`: local input, discovery, path, transport-limit, or envelope validation error;
- `3`: valid envelope with terminal status other than `SUCCESS`;
- `4`: wrapper timeout or nonzero Antigravity process exit.

On wrapper timeout, only the created process group/tree is terminated, then killed after grace and reaped. Diagnostic content is not echoed; only its character count is reported.

## Conversations and structured output

Use `--conversation <id>` for an explicit follow-up. `--continue` is safe only when one relevant recent conversation exists in that workspace. Pass `--json-schema <path>` for an output contract supported by the installed CLI. Use `--response-only` only when losing envelope metadata is acceptable after validation.

The wrapper exposes `--mode plan|accept-edits|auto`, current model/effort/agent options, `--add-dir`, `--disable-slash-commands`, and `--sandbox`; none expands the user's authorization, and availability remains CLI/platform dependent.

