---
artifact: wop-wave-prompt
plan_id: 11111111-1111-4111-8111-111111111111
plan_version: 1
plan_title: "Release Evidence Pipeline"
wave_id: W001
authorized_items: "I001,I002"
non_authorized_items: "I003,I004"
predecessor_waves: none
blocked_successor_waves: "W002,W003"
language: en
source_readme: README.md
source_readme_sha256: e45155d5de5c7ddb867e36b782626afcb0c89258718579fc0cfe879bad34a8b7
---

# Wave W001 — Contract Discovery

<!-- wop:prompt-section global_protocol -->
## Execution Protocol <!-- wop:section execution_protocol -->

Execute only the assigned wave. Respect ownership boundaries and the strict wave barrier. Do not release a successor from file existence alone; verify predecessor evidence and gate approval. Report deviations and never claim acceptance without produced evidence.

<!-- wop:prompt-section execution_scope -->
<!-- wop:prompt-assigned-wave W001 -->
### General Objective <!-- wop:field general_objective -->

Freeze the release contract and evidence inventory.

### Requirements Addressed <!-- wop:field requirements_addressed -->

- R001

### Wave Execution Instructions <!-- wop:field execution_instructions -->

Execute only I001 and I002 in W001, in parallel under their exclusive ownership boundaries, then integrate both results at the gate.

### Parallelism Rationale <!-- wop:field parallelism_rationale -->

I001 writes contract.md while I002 writes inventory.md; neither consumes or modifies the other's output.

### Ownership Boundaries <!-- wop:field ownership_boundaries -->

I001 owns contract.md. I002 owns inventory.md.

<!-- wop:prompt-assigned-item I001 -->
#### Item I001 — Define Contract

##### Objective <!-- wop:field objective -->

Define the required release-evidence fields.

##### Context <!-- wop:field context -->

The manifest must be portable and auditable.

##### Inputs and Prerequisites <!-- wop:field inputs_prerequisites -->

Use R001 and the global contracts.

##### Scope <!-- wop:field scope -->

Create contract.md only.

##### Ownership <!-- wop:field ownership -->

Exclusive ownership of contract.md.

##### Outputs <!-- wop:field outputs -->

- contract.md

##### Restrictions <!-- wop:field restrictions -->

- Do not edit inventory.md or start W002.

<!-- wop:prompt-assigned-item I002 -->
#### Item I002 — Inventory Evidence

##### Objective <!-- wop:field objective -->

Inventory the expected evidence sources.

##### Context <!-- wop:field context -->

The inventory is an input to manifest generation.

##### Inputs and Prerequisites <!-- wop:field inputs_prerequisites -->

Use R001 and the stated scope.

##### Scope <!-- wop:field scope -->

Create inventory.md only.

##### Ownership <!-- wop:field ownership -->

Exclusive ownership of inventory.md.

##### Outputs <!-- wop:field outputs -->

- inventory.md

##### Restrictions <!-- wop:field restrictions -->

- Do not edit contract.md or start W002.

<!-- wop:prompt-section predecessor_verification -->
### Prerequisites <!-- wop:field prerequisites -->

No predecessor wave.

<!-- wop:prompt-section shared_context -->
## Outcome <!-- wop:section outcome -->

Deliver a reproducible release-evidence bundle with a verified manifest and acceptance report.

## Execution Context <!-- wop:section execution_context -->

The example uses only UTF-8 Markdown files and demonstrates parallel discovery followed by implementation and verification.

## Confirmed Facts <!-- wop:section confirmed_facts -->

- The package has three strictly ordered waves.
- I001 and I002 own different artifacts and may run concurrently.

## Scope <!-- wop:section scope -->

Create a release contract, evidence inventory, manifest, and acceptance report. Product deployment is outside scope.

## Stakeholders and Authority <!-- wop:section stakeholders -->

- Release owner approves the final report.
- Item owners may modify only their named outputs.

## Requirements <!-- wop:section requirements -->

- R001: Define the release-evidence contract.
- R002: Produce a manifest conforming to that contract.
- R003: Verify the manifest and retain actual results.

## Constraints <!-- wop:section constraints -->

- Do not start a later wave before the predecessor gate passes.
- Do not claim evidence that was not produced.

## Decisions <!-- wop:section decisions -->

- Markdown is the portable evidence format for this example.

## Assumptions <!-- wop:section assumptions -->

- The execution workspace is writable.

## Unknowns <!-- wop:section unknowns -->

None. A newly discovered material unknown blocks affected work and requires a plan revision or bounded discovery.

## Risks <!-- wop:section risks -->

- Contract drift: freeze the W001 handoff and stop W002 if it changes.
- Partial generation: retain the prior accepted artifact and report the failed check.

## Environments and Operations <!-- wop:section operations -->

Run in a disposable project workspace. Preserve command output or inspection results next to the acceptance report.

## Global Contracts <!-- wop:section global_contracts -->

- All files are UTF-8 with LF line endings.
- Evidence records identify the check, actual result, actor, and artifact path.

## Dependency Map <!-- wop:section dependency_map -->

I001 and I002 are independent within W001. W002 depends on approved W001 outputs. W003 depends on approved W002 output and evidence.

## Requirement Traceability <!-- wop:section requirement_traceability -->

| Requirement | Items | Outputs | Verification |
|---|---|---|---|
| R001 | I001, I002 | contract.md, inventory.md | review and completeness results |
| R002 | I003 | manifest.md | conformance and coverage results |
| R003 | I004 | acceptance-report.md | end-to-end results and decision reference |

## Verification Strategy <!-- wop:section verification_strategy -->

Review each item output, evaluate each wave gate from actual evidence, then inspect traceability and contract conformance end to end.

## Rollback and Recovery <!-- wop:section rollback_recovery -->

On a failed write or check, preserve the last accepted artifact, isolate the failed candidate, record exact paths and results, and do not release the next wave.

## Final Acceptance <!-- wop:section final_acceptance -->

R001-R003 are satisfied, all wave gates passed, the acceptance report references actual evidence, and the release owner records a decision.

## Compatibility Decision <!-- wop:section compatibility_decision -->

Preserve the existing evidence field names so downstream release tooling remains backward compatible.

<!-- wop:prompt-section completion_contract -->
### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- Contract and inventory are complete, mutually consistent, and reviewable.

### Completion Gate <!-- wop:field completion_gate -->

I001 and I002 are accepted with evidence; their outputs do not conflict.

### Evidence Requirements <!-- wop:field evidence_requirements -->

Retain contract review and inventory completeness results.

### Integration and Handoff <!-- wop:field integration_handoff -->

Publish contract.md, inventory.md, their evidence, and the approved W001 gate to W002.

<!-- wop:prompt-completion-item I001 -->
#### Item I001 — Define Contract

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- Every required evidence field has a definition and validation rule.

##### Verification Evidence <!-- wop:field verification_evidence -->

Record a field-by-field review result.

##### Handoff Requirements <!-- wop:field handoff_requirements -->

Publish contract.md and its review evidence.

<!-- wop:prompt-completion-item I002 -->
#### Item I002 — Inventory Evidence

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- Every in-scope evidence source has an owner and expected location.

##### Verification Evidence <!-- wop:field verification_evidence -->

Record a completeness inspection against scope.

##### Handoff Requirements <!-- wop:field handoff_requirements -->

Publish inventory.md and its inspection evidence.
