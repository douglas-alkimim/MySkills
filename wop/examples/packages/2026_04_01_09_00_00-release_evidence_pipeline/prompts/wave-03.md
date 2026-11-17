---
artifact: wop-wave-prompt
plan_id: 11111111-1111-4111-8111-111111111111
plan_version: 1
plan_title: "Release Evidence Pipeline"
wave_id: W003
authorized_items: I004
non_authorized_items: "I001,I002,I003"
predecessor_waves: W002
blocked_successor_waves: none
language: en
source_readme: README.md
source_readme_sha256: e45155d5de5c7ddb867e36b782626afcb0c89258718579fc0cfe879bad34a8b7
---

# Wave W003 — Verify Bundle

<!-- wop:prompt-section global_protocol -->
## Execution Protocol <!-- wop:section execution_protocol -->

Execute only the assigned wave. Respect ownership boundaries and the strict wave barrier. Do not release a successor from file existence alone; verify predecessor evidence and gate approval. Report deviations and never claim acceptance without produced evidence.

<!-- wop:prompt-section execution_scope -->
<!-- wop:prompt-assigned-wave W003 -->
### General Objective <!-- wop:field general_objective -->

Verify the complete bundle and produce final acceptance evidence.

### Requirements Addressed <!-- wop:field requirements_addressed -->

- R003

### Wave Execution Instructions <!-- wop:field execution_instructions -->

Execute only I004 in W003 after predecessor verification; inspect prior artifacts read-only and produce acceptance-report.md.

### Parallelism Rationale <!-- wop:field parallelism_rationale -->

One item owns integrated verification to avoid conflicting final decisions.

### Ownership Boundaries <!-- wop:field ownership_boundaries -->

I004 owns acceptance-report.md and reads all prior artifacts without modifying them.

<!-- wop:prompt-assigned-item I004 -->
#### Item I004 — Verify and Report

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

##### Restrictions <!-- wop:field restrictions -->

- Stop and report any failed criterion; do not fabricate acceptance.

<!-- wop:prompt-section predecessor_verification -->
### Prerequisites <!-- wop:field prerequisites -->

W002 output, evidence, criteria, and completion gate must be approved.

<!-- wop:prompt-predecessor W002 -->
## Wave W002 — Build Manifest

### General Objective <!-- wop:field general_objective -->

Create the release manifest from approved contract and inventory outputs.

### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- The manifest conforms to every frozen contract rule and covers the inventory.

### Completion Gate <!-- wop:field completion_gate -->

I003 is accepted with conformance evidence and the manifest is ready for independent verification.

### Evidence Requirements <!-- wop:field evidence_requirements -->

Retain the conformance result and manifest coverage result.

### Integration and Handoff <!-- wop:field integration_handoff -->

Publish manifest.md, conformance evidence, and the approved W002 gate to W003.

<!-- wop:prompt-predecessor-item I003 -->
#### Item I003 — Generate Manifest

##### Outputs <!-- wop:field outputs -->

- manifest.md

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- Every inventory entry maps to a valid manifest record.

##### Verification Evidence <!-- wop:field verification_evidence -->

Record contract conformance and coverage results.

##### Handoff Requirements <!-- wop:field handoff_requirements -->

Publish manifest.md and both actual results.

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

## Final Report Restrictions <!-- wop:section final_report_restrictions scope=item items=I004 -->

The final report may reference predecessor artifacts but must not modify them.

<!-- wop:prompt-section completion_contract -->
### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- All requirements are traceable and the bundle passes end-to-end inspection.

### Completion Gate <!-- wop:field completion_gate -->

I004 is accepted and the release owner has enough produced evidence to decide final acceptance.

### Evidence Requirements <!-- wop:field evidence_requirements -->

Retain actual end-to-end results and the release owner's decision reference.

### Integration and Handoff <!-- wop:field integration_handoff -->

Publish the final report, evidence references, decision, deviations, and residual risks.

<!-- wop:prompt-completion-item I004 -->
#### Item I004 — Verify and Report

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- The report records every check, actual result, evidence location, and final decision.

##### Verification Evidence <!-- wop:field verification_evidence -->

Retain the completed report and referenced inspection outputs.

##### Handoff Requirements <!-- wop:field handoff_requirements -->

Provide the release owner with the report and evidence references.
