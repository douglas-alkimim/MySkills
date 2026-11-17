# Planning Process

## 1. Understand

Extract the outcome, deliverables, scope boundaries, users, systems, environment, constraints, existing decisions, compatibility, and definition of done. Preserve exact identifiers, paths, values, and domain terminology. Select the plan language using the policy in SKILL.md.

## 2. Clarify

Inspect discoverable context before asking. Interview only when an unresolved user decision can materially change scope, architecture, acceptance, risk, or ordering. Use interaction/question-strategy.md. Record answers as facts or decisions rather than conversational residue.

## 3. Investigate

Inspect accessible project files, schemas, interfaces, environments, data, and existing plans. Record only findings that affect execution. State access limitations. Convert discoverable unknowns into bounded discovery items with outputs and gates.

## 4. Decompose

Create the fewest bounded items that fully express the work. An item may omit conditional detail that does not affect execution at the selected planning depth. Split only when subdivision creates genuinely independent execution, improves verification, or reduces risk; keep cohesive work together when fragments would require continuous coordination. Do not create an item for every implementation action.

## 5. Analyze dependencies

Classify output, decision, contract, file-write, shared-resource, integration, and external dependencies. Build the dependency graph before assigning waves. Follow dependency-analysis.md.

## 6. Construct waves

Topologically layer the real graph. Resolve interference edges even when no data dependency exists. Maximize useful safe concurrency within each layer, but do not create artificial waves to display sophistication. A single-wave plan and a single-item wave are valid. Define the strict completion gate before releasing the next layer.

## 7. Specify

Complete every required field for the selected complexity and every conditional field that affects execution. Define shared contracts once when they exist and copy execution-critical portions into generated prompts. Keep requirements traceable directly in Compact and through matrices or full traceability at higher depths.

## 8. Audit

Apply the audit depth selected in adaptive-planning.md. Universal invariants, final acceptance, and workspace integrity remain mandatory; independence becomes pairwise only when items coexist. Mechanical validation supplements but does not replace semantic judgment. Use a concise summary when a simple plan has no findings.

## 9. Persist

Initialize the project workspace, write README.md, generate prompts, validate, register SQLite, and set ready only after all required checks pass.

## 10. Deliver

Report title, stable ID, path, version, plan status, execution status, acceptance status, language, validation result, and any unresolved unknown or manual semantic check.
