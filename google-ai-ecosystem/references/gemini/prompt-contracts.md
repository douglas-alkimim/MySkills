# Gemini Prompt Contracts

Use these as content contracts, not rigid prose. Preserve the user's request and include only authorized context. The helper `scripts/build_gemini_prompt.py` produces equivalent contracts from direct arguments or a JSON request file.

## Explicit task bridge

```text
MASTER TASK-BRIDGE INSTRUCTIONS
Act as a specialist producing an artifact for a local coding agent to integrate.

GOAL
<one concrete outcome>

AUTHORIZED CONTEXT
<minimum repository facts/files/constraints>

USER TASK
<original task>

OUTPUT CONTRACT
- Return <complete file | patch | JSON | bounded plan>.
- Identify target files, evidence, assumptions, and uncertainty.
- Do not claim to have modified local files or performed external actions.
- Mark missing information instead of guessing.

ACCEPTANCE CRITERIA
<tests and invariants>
```

## Image

```text
MASTER INSTRUCTIONS — GEMINI IMAGE GENERATION
Generate the requested image now. Preserve the user's creative intent.

USER REQUEST
<original prompt>

UPLOADED REFERENCES
<numbered filename, purpose, optional description>

OUTPUT CONTRACT
- Use each reference only for its declared purpose.
- Preserve requested identity, composition, style, and text requirements.
- Do not add visible text unless requested.
- Return the generated image, not an explanation or prompt rewrite.
```

## Video

```text
MASTER INSTRUCTIONS — GEMINI VIDEO GENERATION
Generate the requested video now. Preserve the user's creative intent.

USER REQUEST
<original prompt>

UPLOADED REFERENCES
<numbered filename, purpose, optional description>

OUTPUT CONTRACT
- Use each reference only for its declared purpose.
- Preserve requested subject and reference continuity.
- Follow specified camera, movement, dialogue/audio, aspect ratio, and duration.
- Return the generated video, not an explanation or prompt rewrite.
```

Never put credentials, cookies, tokens, browser state, or unrelated private context into a contract or evidence log.

