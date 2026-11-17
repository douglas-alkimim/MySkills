---
artifact: wop-wave-prompt
plan_id: 11111111-1111-4111-8111-111111111111
plan_version: 1
plan_title: "Release Evidence Pipeline"
wave_id: W002
authorized_items: I003
non_authorized_items: "I001,I002,I004"
predecessor_waves: W001
blocked_successor_waves: W003
language: en
source_readme: README.md
source_readme_sha256: e45155d5de5c7ddb867e36b782626afcb0c89258718579fc0cfe879bad34a8b7
---

# Wave W002 — Build Manifest

<!-- wop:prompt-section global_protocol -->
## Execution Protocol <!-- wop:section execution_protocol -->

Execute only the assigned wave. Respect ownership boundaries and the strict wave barrier. Do not release a successor from file existence alone; verify predecessor evidence and gate approval. Report deviations and never claim acceptance without produced evidence.

<!-- wop:prompt-section execution_scope -->
<!-- wop:prompt-assigned-wave W002 -->
### General Objective <!-- wop:field general_objective -->

Create the release manifest from approved contract and inventory outputs.

### Requirements Addressed <!-- wop:field requirements_addressed -->

- R002

### Wave Execution Instructions <!-- wop:field execution_instructions -->

Execute only I003 in W002 after predecessor verification; produce and verify manifest.md without modifying frozen inputs.

### Parallelism Rationale <!-- wop:field parallelism_rationale -->

This wave has one item because manifest construction integrates both predecessor outputs.

### Ownership Boundaries <!-- wop:field ownership_boundaries -->

I003 owns manifest.md and must not modify frozen W001 artifacts.

<!-- wop:prompt-assigned-item I003 -->
#### Item I003 — Generate Manifest

##### Objective <!-- wop:field objective -->

Produce a contract-conforming manifest.

##### Context <!-- wop:field context -->

W001 defines the frozen schema and source inventory.

##### Inputs and Prerequisites <!-- wop:field inputs_prerequisites -->

Require approved contract.md, inventory.md, their evidence, and the W001 gate.

##### Scope <!-- wop:field scope -->

Create manifest.md only.

##### Ownership <!-- wop:field ownership -->

Exclusive ownership of manifest.md.

##### Outputs <!-- wop:field outputs -->

- manifest.md

##### Restrictions <!-- wop:field restrictions -->

- Do not change W001 outputs or start W003.

<!-- wop:prompt-section predecessor_verification -->
### Prerequisites <!-- wop:field prerequisites -->

W001 outputs, evidence, criteria, and completion gate must be approved.

<!-- wop:prompt-predecessor W001 -->
## Wave W001 — Contract Discovery

### General Objective <!-- wop:field general_objective -->

Freeze the release contract and evidence inventory.

### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- Contract and inventory are complete, mutually consistent, and reviewable.

### Completion Gate <!-- wop:field completion_gate -->

I001 and I002 are accepted with evidence; their outputs do not conflict.

### Evidence Requirements <!-- wop:field evidence_requirements -->

Retain contract review and inventory completeness results.

### Integration and Handoff <!-- wop:field integration_handoff -->

Publish contract.md, inventory.md, their evidence, and the approved W001 gate to W002.

<!-- wop:prompt-predecessor-item I001 -->
#### Item I001 — Define Contract

##### Outputs <!-- wop:field outputs -->

- contract.md

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- Every required evidence field has a definition and validation rule.

##### Verification Evidence <!-- wop:field verification_evidence -->

Record a field-by-field review result.

##### Handoff Requirements <!-- wop:field handoff_requirements -->

Publish contract.md and its review evidence.

<!-- wop:prompt-predecessor-item I002 -->
#### Item I002 — Inventory Evidence

##### Outputs <!-- wop:field outputs -->

- inventory.md

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- Every in-scope evidence source has an owner and expected location.

##### Verification Evidence <!-- wop:field verification_evidence -->

Record a completeness inspection against scope.

##### Handoff Requirements <!-- wop:field handoff_requirements -->

Publish inventory.md and its inspection evidence.

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

## Manifest Construction Notes <!-- wop:section manifest_construction scope=wave waves=W002 -->

Build the manifest only from the frozen contract and inventory accepted at the W001 gate.

<!-- wop:prompt-section completion_contract -->
### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- The manifest conforms to every frozen contract rule and covers the inventory.

### Completion Gate <!-- wop:field completion_gate -->

I003 is accepted with conformance evidence and the manifest is ready for independent verification.

### Evidence Requirements <!-- wop:field evidence_requirements -->

Retain the conformance result and manifest coverage result.

### Integration and Handoff <!-- wop:field integration_handoff -->

Publish manifest.md, conformance evidence, and the approved W002 gate to W003.

<!-- wop:prompt-completion-item I003 -->
#### Item I003 — Generate Manifest

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- Every inventory entry maps to a valid manifest record.

##### Verification Evidence <!-- wop:field verification_evidence -->

Record contract conformance and coverage results.

##### Handoff Requirements <!-- wop:field handoff_requirements -->

Publish manifest.md and both actual results.
