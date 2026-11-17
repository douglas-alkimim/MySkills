---
plan_id: <canonical-lowercase-uuid>
title: <plan-title>
version: 1
language: <language-tag>
complexity: standard
plan_status: draft
execution_status: not_started
acceptance_status: not_evaluated
created_at: <iso-8601-with-offset>
updated_at: <iso-8601-with-offset>
---

# <Plan Title>

<!-- Standard is the default for ordinary multi-deliverable work. Omit a conditional section when it is genuinely irrelevant; never retain it as empty boilerplate or repeat information already authoritative elsewhere. Keep the fewest waves and items justified by real dependencies, independent deliverables, verification, or risk. -->

## Outcome <!-- wop:section outcome -->

<Observable outcome and complete deliverables.>

## Execution Context <!-- wop:section execution_context -->

<Only the project, user, system, environment, current-state, and inspected evidence that changes execution.>

## Confirmed Facts <!-- wop:section confirmed_facts -->

- F001: <Relevant fact and source. Omit this section when no confirmed fact needs separate emphasis.>

## Scope <!-- wop:section scope -->

### In scope

- <Bounded work.>

### Out of scope

- <Excluded work.>

## Assumptions <!-- wop:section assumptions -->

- A001: <Material assumption, impact, and validation. Omit this section when no assumption affects execution.>

## Unknowns <!-- wop:section unknowns -->

- U001: <Material unknown, owner, resolution method, latest resolution point, and blocker effect. Omit this section when none remains.>

## Requirements <!-- wop:section requirements -->

- R001: <Requirement in testable language.>

## Constraints <!-- wop:section constraints -->

- C001: <Constraint and source.>

## Decisions <!-- wop:section decisions -->

- D001: <Decision, rationale, owner, and alternatives.>

## Global Contracts <!-- wop:section global_contracts -->

- GC001: <Interface, data, terminology, ownership, or quality contract shared by waves.>

<!-- Custom sections may use scope=global, scope=wave waves=WNNN,..., or scope=item items=INNN,...; omitted scope defaults to global. -->

## Wave Sequence <!-- wop:section wave_sequence -->

1. W001 — <Name>: <why it is first>.
2. W002 — <Name>: <outputs and gates required from W001>.

## Wave W001 — <Name> <!-- wop:wave W001 -->

### General Objective <!-- wop:field general_objective -->

<Wave outcome.>

### Prerequisites <!-- wop:field prerequisites -->

No predecessor wave. <Other inputs that must exist before release.>

### Requirements Addressed <!-- wop:field requirements_addressed -->

- R001

### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- <Observable wave pass condition.>

### Completion Gate <!-- wop:field completion_gate -->

Every item is complete, individually accepted, integrated where needed, and all general criteria pass with evidence.

### Evidence Requirements <!-- wop:field evidence_requirements -->

- <Evidence retained for the gate.>

### Parallelism Rationale <!-- wop:field parallelism_rationale -->

<Pairwise explanation of independent inputs, outputs, writes, resources, decisions, and integration.>

### Ownership Boundaries <!-- wop:field ownership_boundaries -->

<Owners and allowed files, artifacts, systems, or effects.>

### Wave Execution Instructions <!-- wop:field execution_instructions -->

Authorize only I001 in W001. Apply its existing item contract and do not start a later wave.

### Integration and Handoff <!-- wop:field integration_handoff -->

<Integration procedure and exact outputs available to W002.>

#### Item I001 — <Name> <!-- wop:item I001 -->

##### Objective <!-- wop:field objective -->

<One bounded result.>

##### Context <!-- wop:field context -->

<Execution-critical facts and contracts not already authoritative in a global section.>

##### Inputs and Prerequisites <!-- wop:field inputs_prerequisites -->

- <Available input.>

##### Scope <!-- wop:field scope -->

- <Required work.>

##### Ownership <!-- wop:field ownership -->

- <Exclusive files, artifacts, or system boundary.>

##### Outputs <!-- wop:field outputs -->

- <Output and location or interface.>

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- <Expected state, observation method, and pass threshold.>

##### Restrictions <!-- wop:field restrictions -->

- <Prohibited change or effect.>

##### Verification Evidence <!-- wop:field verification_evidence -->

- <Command, inspection, or record with expected result.>

##### Handoff Requirements <!-- wop:field handoff_requirements -->

- <Only the output contract a downstream consumer needs.>

## Wave W002 — <Name> <!-- wop:wave W002 -->

### General Objective <!-- wop:field general_objective -->

<Wave outcome.>

### Prerequisites <!-- wop:field prerequisites -->

W001 must have passed its completion gate. Verify its outputs, contracts, and evidence before work.

### Requirements Addressed <!-- wop:field requirements_addressed -->

- R001

### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- <Observable wave pass condition.>

### Completion Gate <!-- wop:field completion_gate -->

Every item is complete, individually accepted, integrated where needed, and all general criteria pass with evidence.

### Evidence Requirements <!-- wop:field evidence_requirements -->

- <Evidence retained for the gate.>

### Parallelism Rationale <!-- wop:field parallelism_rationale -->

<Pairwise independence or reason for one item.>

### Ownership Boundaries <!-- wop:field ownership_boundaries -->

<Owners and allowed changes.>

### Wave Execution Instructions <!-- wop:field execution_instructions -->

After predecessor verification, authorize only I002 in W002 and do not start a later wave.

### Integration and Handoff <!-- wop:field integration_handoff -->

<Final integration and handoff.>

#### Item I002 — <Name> <!-- wop:item I002 -->

##### Objective <!-- wop:field objective -->

<One bounded result.>

##### Context <!-- wop:field context -->

<Execution-critical facts and predecessor contracts.>

##### Inputs and Prerequisites <!-- wop:field inputs_prerequisites -->

- <Accepted W001 output and evidence.>

##### Scope <!-- wop:field scope -->

- <Required work.>

##### Ownership <!-- wop:field ownership -->

- <Exclusive boundary.>

##### Outputs <!-- wop:field outputs -->

- <Output.>

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- <Expected state, method, and threshold.>

##### Restrictions <!-- wop:field restrictions -->

- Do not change an accepted predecessor contract without a plan revision.

##### Verification Evidence <!-- wop:field verification_evidence -->

- <Evidence.>

##### Handoff Requirements <!-- wop:field handoff_requirements -->

- <Final report or downstream output.>

## Requirement Traceability <!-- wop:section requirement_traceability -->

| Requirement | Responsible items | Outputs | Verification evidence |
|---|---|---|---|
| R001 | I001, I002 | <outputs> | <criteria/evidence> |

## Dependency Map <!-- wop:section dependency_map -->

| From | To | Type | Reason | Gate evidence |
|---|---|---|---|---|
| W001 | W002 | output/contract | <reason> | <evidence> |

## Verification Strategy <!-- wop:section verification_strategy -->

<Item, integration, end-to-end, domain, and environment verification.>

## Final Acceptance <!-- wop:section final_acceptance -->

- <Condition that proves the outcome and deliverables.>

## Execution Protocol <!-- wop:section execution_protocol -->

Identify the package and read `README.md` plus every referenced wave prompt. Execute waves strictly in order. Within a wave, parallelize only the items proven independent. Wait for every item, integrate outputs, collect evidence, and evaluate the completion gate before releasing the next wave. Stop on a failed gate or material scope change, and perform final acceptance after the last wave.

## Revision History <!-- wop:section revision_history -->

- Version 1 — <timestamp> — Initial plan — <source/author>.
