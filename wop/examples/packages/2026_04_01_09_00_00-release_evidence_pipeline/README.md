---
plan_id: 11111111-1111-4111-8111-111111111111
title: Release Evidence Pipeline
version: 1
language: en
complexity: standard
plan_status: ready
execution_status: not_started
acceptance_status: not_evaluated
created_at: 2026-04-01T09:00:00-03:00
updated_at: 2026-04-01T09:00:00-03:00
---

# Release Evidence Pipeline

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

## Assumptions <!-- wop:section assumptions -->

- The execution workspace is writable.

## Unknowns <!-- wop:section unknowns -->

None. A newly discovered material unknown blocks affected work and requires a plan revision or bounded discovery.

## Requirements <!-- wop:section requirements -->

- R001: Define the release-evidence contract.
- R002: Produce a manifest conforming to that contract.
- R003: Verify the manifest and retain actual results.

## Constraints <!-- wop:section constraints -->

- Do not start a later wave before the predecessor gate passes.
- Do not claim evidence that was not produced.

## Decisions <!-- wop:section decisions -->

- Markdown is the portable evidence format for this example.

## Risks <!-- wop:section risks -->

- Contract drift: freeze the W001 handoff and stop W002 if it changes.
- Partial generation: retain the prior accepted artifact and report the failed check.

## Environments and Operations <!-- wop:section operations -->

Run in a disposable project workspace. Preserve command output or inspection results next to the acceptance report.

## Global Contracts <!-- wop:section global_contracts -->

- All files are UTF-8 with LF line endings.
- Evidence records identify the check, actual result, actor, and artifact path.

## Compatibility Decision <!-- wop:section compatibility_decision -->

Preserve the existing evidence field names so downstream release tooling remains backward compatible.

## Manifest Construction Notes <!-- wop:section manifest_construction scope=wave waves=W002 -->

Build the manifest only from the frozen contract and inventory accepted at the W001 gate.

## Final Report Restrictions <!-- wop:section final_report_restrictions scope=item items=I004 -->

The final report may reference predecessor artifacts but must not modify them.

## Wave Sequence <!-- wop:section wave_sequence -->

1. W001 defines the contract and inventories evidence in parallel.
2. W002 creates the manifest from approved W001 outputs.
3. W003 verifies the complete bundle and produces final acceptance evidence.

## Wave W001 — Contract Discovery <!-- wop:wave W001 -->

### General Objective <!-- wop:field general_objective -->

Freeze the release contract and evidence inventory.

### Prerequisites <!-- wop:field prerequisites -->

No predecessor wave.

### Requirements Addressed <!-- wop:field requirements_addressed -->

- R001

### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- Contract and inventory are complete, mutually consistent, and reviewable.

### Completion Gate <!-- wop:field completion_gate -->

I001 and I002 are accepted with evidence; their outputs do not conflict.

### Evidence Requirements <!-- wop:field evidence_requirements -->

Retain contract review and inventory completeness results.

### Parallelism Rationale <!-- wop:field parallelism_rationale -->

I001 writes contract.md while I002 writes inventory.md; neither consumes or modifies the other's output.

### Ownership Boundaries <!-- wop:field ownership_boundaries -->

I001 owns contract.md. I002 owns inventory.md.

### Wave Execution Instructions <!-- wop:field execution_instructions -->

Execute only I001 and I002 in W001, in parallel under their exclusive ownership boundaries, then integrate both results at the gate.

### Integration and Handoff <!-- wop:field integration_handoff -->

Publish contract.md, inventory.md, their evidence, and the approved W001 gate to W002.

#### Item I001 — Define Contract <!-- wop:item I001 -->

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

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- Every required evidence field has a definition and validation rule.

##### Restrictions <!-- wop:field restrictions -->

- Do not edit inventory.md or start W002.

##### Verification Evidence <!-- wop:field verification_evidence -->

Record a field-by-field review result.

##### Handoff Requirements <!-- wop:field handoff_requirements -->

Publish contract.md and its review evidence.

#### Item I002 — Inventory Evidence <!-- wop:item I002 -->

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

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- Every in-scope evidence source has an owner and expected location.

##### Restrictions <!-- wop:field restrictions -->

- Do not edit contract.md or start W002.

##### Verification Evidence <!-- wop:field verification_evidence -->

Record a completeness inspection against scope.

##### Handoff Requirements <!-- wop:field handoff_requirements -->

Publish inventory.md and its inspection evidence.

## Wave W002 — Build Manifest <!-- wop:wave W002 -->

### General Objective <!-- wop:field general_objective -->

Create the release manifest from approved contract and inventory outputs.

### Prerequisites <!-- wop:field prerequisites -->

W001 outputs, evidence, criteria, and completion gate must be approved.

### Requirements Addressed <!-- wop:field requirements_addressed -->

- R002

### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- The manifest conforms to every frozen contract rule and covers the inventory.

### Completion Gate <!-- wop:field completion_gate -->

I003 is accepted with conformance evidence and the manifest is ready for independent verification.

### Evidence Requirements <!-- wop:field evidence_requirements -->

Retain the conformance result and manifest coverage result.

### Parallelism Rationale <!-- wop:field parallelism_rationale -->

This wave has one item because manifest construction integrates both predecessor outputs.

### Ownership Boundaries <!-- wop:field ownership_boundaries -->

I003 owns manifest.md and must not modify frozen W001 artifacts.

### Wave Execution Instructions <!-- wop:field execution_instructions -->

Execute only I003 in W002 after predecessor verification; produce and verify manifest.md without modifying frozen inputs.

### Integration and Handoff <!-- wop:field integration_handoff -->

Publish manifest.md, conformance evidence, and the approved W002 gate to W003.

#### Item I003 — Generate Manifest <!-- wop:item I003 -->

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

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- Every inventory entry maps to a valid manifest record.

##### Restrictions <!-- wop:field restrictions -->

- Do not change W001 outputs or start W003.

##### Verification Evidence <!-- wop:field verification_evidence -->

Record contract conformance and coverage results.

##### Handoff Requirements <!-- wop:field handoff_requirements -->

Publish manifest.md and both actual results.

## Wave W003 — Verify Bundle <!-- wop:wave W003 -->

### General Objective <!-- wop:field general_objective -->

Verify the complete bundle and produce final acceptance evidence.

### Prerequisites <!-- wop:field prerequisites -->

W002 output, evidence, criteria, and completion gate must be approved.

### Requirements Addressed <!-- wop:field requirements_addressed -->

- R003

### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- All requirements are traceable and the bundle passes end-to-end inspection.

### Completion Gate <!-- wop:field completion_gate -->

I004 is accepted and the release owner has enough produced evidence to decide final acceptance.

### Evidence Requirements <!-- wop:field evidence_requirements -->

Retain actual end-to-end results and the release owner's decision reference.

### Parallelism Rationale <!-- wop:field parallelism_rationale -->

One item owns integrated verification to avoid conflicting final decisions.

### Ownership Boundaries <!-- wop:field ownership_boundaries -->

I004 owns acceptance-report.md and reads all prior artifacts without modifying them.

### Wave Execution Instructions <!-- wop:field execution_instructions -->

Execute only I004 in W003 after predecessor verification; inspect prior artifacts read-only and produce acceptance-report.md.

### Integration and Handoff <!-- wop:field integration_handoff -->

Publish the final report, evidence references, decision, deviations, and residual risks.

#### Item I004 — Verify and Report <!-- wop:item I004 -->

##### Objective <!-- wop:field objective -->

Verify the bundle and document the actual outcome.

##### Context <!-- wop:field context -->

Final acceptance must not be inferred from planned evidence.

##### Inputs and Prerequisites <!-- wop:field inputs_prerequisites -->

Require approved manifest.md and W002 conformance evidence.

##### Scope <!-- wop:field scope -->

Create acceptance-report.md; do not repair predecessor artifacts silently.

##### Ownership <!-- wop:field ownership -->

Exclusive ownership of acceptance-report.md.

##### Outputs <!-- wop:field outputs -->

- acceptance-report.md

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- The report records every check, actual result, evidence location, and final decision.

##### Restrictions <!-- wop:field restrictions -->

- Stop and report any failed criterion; do not fabricate acceptance.

##### Verification Evidence <!-- wop:field verification_evidence -->

Retain the completed report and referenced inspection outputs.

##### Handoff Requirements <!-- wop:field handoff_requirements -->

Provide the release owner with the report and evidence references.

## Requirement Traceability <!-- wop:section requirement_traceability -->

| Requirement | Items | Outputs | Verification |
|---|---|---|---|
| R001 | I001, I002 | contract.md, inventory.md | review and completeness results |
| R002 | I003 | manifest.md | conformance and coverage results |
| R003 | I004 | acceptance-report.md | end-to-end results and decision reference |

## Dependency Map <!-- wop:section dependency_map -->

I001 and I002 are independent within W001. W002 depends on approved W001 outputs. W003 depends on approved W002 output and evidence.

## Verification Strategy <!-- wop:section verification_strategy -->

Review each item output, evaluate each wave gate from actual evidence, then inspect traceability and contract conformance end to end.

## Rollback and Recovery <!-- wop:section rollback_recovery -->

On a failed write or check, preserve the last accepted artifact, isolate the failed candidate, record exact paths and results, and do not release the next wave.

## Final Acceptance <!-- wop:section final_acceptance -->

R001-R003 are satisfied, all wave gates passed, the acceptance report references actual evidence, and the release owner records a decision.

## Execution Protocol <!-- wop:section execution_protocol -->

Execute only the assigned wave. Respect ownership boundaries and the strict wave barrier. Do not release a successor from file existence alone; verify predecessor evidence and gate approval. Report deviations and never claim acceptance without produced evidence.

## Revision History <!-- wop:section revision_history -->

- Version 1, 2026-04-01: initial complete English example.
