---
artifact: wop-execute-all
plan_id: 11111111-1111-4111-8111-111111111111
plan_version: 1
plan_title: "Release Evidence Pipeline"
language: en
source_readme: README.md
source_readme_sha256: e45155d5de5c7ddb867e36b782626afcb0c89258718579fc0cfe879bad34a8b7
---

# Release Evidence Pipeline

<!-- wop:prompt-section wave_prompts -->
- prompts/wave-01.md — W001 — Contract Discovery
- prompts/wave-02.md — W002 — Build Manifest
- prompts/wave-03.md — W003 — Verify Bundle

<!-- wop:prompt-section orchestration -->
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

## Wave Sequence <!-- wop:section wave_sequence -->

1. W001 defines the contract and inventories evidence in parallel.
2. W002 creates the manifest from approved W001 outputs.
3. W003 verifies the complete bundle and produces final acceptance evidence.

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

## Execution Protocol <!-- wop:section execution_protocol -->

Execute only the assigned wave. Respect ownership boundaries and the strict wave barrier. Do not release a successor from file existence alone; verify predecessor evidence and gate approval. Report deviations and never claim acceptance without produced evidence.

## Compatibility Decision <!-- wop:section compatibility_decision -->

Preserve the existing evidence field names so downstream release tooling remains backward compatible.
