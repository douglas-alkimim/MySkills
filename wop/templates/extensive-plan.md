---
plan_id: <canonical-lowercase-uuid>
title: <plan-title>
version: 1
language: <language-tag>
complexity: extensive
plan_status: draft
execution_status: not_started
acceptance_status: not_evaluated
created_at: <iso-8601-with-offset>
updated_at: <iso-8601-with-offset>
---

# <Plan Title>

<!-- Use this template only when risk, uncertainty, systems, disciplines, external effects, regulation, recovery difficulty, or coordination justify its additional controls. Keep detailed sections relevant to the actual consequences; depth does not justify artificial waves, items, or agents. -->

## Outcome <!-- wop:section outcome -->

<Outcome, deliverables, and business or research effect.>

## Execution Context <!-- wop:section execution_context -->

<Systems, repositories, stakeholders, environments, current state, and inspected evidence.>

## Confirmed Facts <!-- wop:section confirmed_facts -->

- F001: <Fact, source, and date.>

## Scope <!-- wop:section scope -->

### In scope

- <Scope.>

### Out of scope

- <Exclusion.>

## Stakeholders and Authority <!-- wop:section stakeholders -->

| Role | Responsibility | Approval or decision boundary |
|---|---|---|
| <role> | <responsibility> | <boundary> |

## Assumptions <!-- wop:section assumptions -->

- A001: <Assumption, impact, validation owner, and deadline.>

## Unknowns <!-- wop:section unknowns -->

- U001: <Unknown, discovery/prototype, owner, evidence, and blocking consequence.>

## Requirements <!-- wop:section requirements -->

- R001: <Requirement.>

## Constraints <!-- wop:section constraints -->

- C001: <Constraint.>

## Decisions <!-- wop:section decisions -->

- D001: <Choice, rationale, alternatives, owner, and revisit trigger.>

## Risks <!-- wop:section risks -->

| Risk | Likelihood | Impact | Prevention | Detection | Response owner |
|---|---|---|---|---|---|
| <risk> | <level> | <level> | <control> | <signal> | <owner> |

## Environments and Operations <!-- wop:section operations -->

<Environment matrix, access, configuration, observability, deployment, rollback, and recovery.>

## Global Contracts <!-- wop:section global_contracts -->

- GC001: <Frozen interface, data, quality, terminology, or ownership contract.>

## Wave Sequence <!-- wop:section wave_sequence -->

1. W001 — <Discovery or foundation>.
2. W002 — <Independent implementation>.
3. W003 — <Integration and verification>.

## Wave W001 — <Name> <!-- wop:wave W001 -->

### General Objective <!-- wop:field general_objective -->

<Objective.>

### Prerequisites <!-- wop:field prerequisites -->

No predecessor wave. <External release conditions.>

### Requirements Addressed <!-- wop:field requirements_addressed -->

- R001

### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- <Criteria.>

### Completion Gate <!-- wop:field completion_gate -->

All items, integrations, risk controls, and criteria pass with evidence and required approval.

### Evidence Requirements <!-- wop:field evidence_requirements -->

- <Evidence and retention location.>

### Parallelism Rationale <!-- wop:field parallelism_rationale -->

<Pairwise independence evidence.>

### Ownership Boundaries <!-- wop:field ownership_boundaries -->

<Agents, people, systems, and allowed changes.>

### Wave Execution Instructions <!-- wop:field execution_instructions -->

Execute only I001 in W001. Apply its ownership, evidence, risk controls, and restrictions; do not start a later wave.

### Integration and Handoff <!-- wop:field integration_handoff -->

<Integration, operational handoff, and frozen outputs.>

#### Item I001 — <Name> <!-- wop:item I001 -->

##### Objective <!-- wop:field objective -->

<Objective.>

##### Context <!-- wop:field context -->

<Context and contracts.>

##### Inputs and Prerequisites <!-- wop:field inputs_prerequisites -->

- <Input.>

##### Scope <!-- wop:field scope -->

- <Work.>

##### Ownership <!-- wop:field ownership -->

- <Boundary.>

##### Outputs <!-- wop:field outputs -->

- <Output.>

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- <State, method, threshold.>

##### Restrictions <!-- wop:field restrictions -->

- <Restriction and authorization boundary.>

##### Verification Evidence <!-- wop:field verification_evidence -->

- <Evidence.>

##### Handoff Requirements <!-- wop:field handoff_requirements -->

- <Handoff.>

## Wave W002 — <Name> <!-- wop:wave W002 -->

### General Objective <!-- wop:field general_objective -->

<Objective.>

### Prerequisites <!-- wop:field prerequisites -->

W001 must pass. Verify named outputs, approvals, and evidence.

### Requirements Addressed <!-- wop:field requirements_addressed -->

- R001

### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- <Criteria.>

### Completion Gate <!-- wop:field completion_gate -->

All items and integrations pass with evidence.

### Evidence Requirements <!-- wop:field evidence_requirements -->

- <Evidence.>

### Parallelism Rationale <!-- wop:field parallelism_rationale -->

<Pairwise evidence.>

### Ownership Boundaries <!-- wop:field ownership_boundaries -->

<Boundaries.>

### Wave Execution Instructions <!-- wop:field execution_instructions -->

Execute only I002 in W002 after predecessor verification. Apply its ownership and restrictions; do not start a later wave.

### Integration and Handoff <!-- wop:field integration_handoff -->

<Handoff.>

#### Item I002 — <Name> <!-- wop:item I002 -->

##### Objective <!-- wop:field objective -->

<Objective.>

##### Context <!-- wop:field context -->

<Context.>

##### Inputs and Prerequisites <!-- wop:field inputs_prerequisites -->

- <Accepted W001 outputs.>

##### Scope <!-- wop:field scope -->

- <Work.>

##### Ownership <!-- wop:field ownership -->

- <Boundary.>

##### Outputs <!-- wop:field outputs -->

- <Output.>

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- <Criteria.>

##### Restrictions <!-- wop:field restrictions -->

- <Restriction.>

##### Verification Evidence <!-- wop:field verification_evidence -->

- <Evidence.>

##### Handoff Requirements <!-- wop:field handoff_requirements -->

- <Handoff.>

## Wave W003 — <Name> <!-- wop:wave W003 -->

### General Objective <!-- wop:field general_objective -->

<Integration, operational readiness, and final verification.>

### Prerequisites <!-- wop:field prerequisites -->

W002 must pass. Verify all predecessor contracts and evidence.

### Requirements Addressed <!-- wop:field requirements_addressed -->

- R001

### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- <End-to-end and operational criteria.>

### Completion Gate <!-- wop:field completion_gate -->

All final checks, risk controls, rollback evidence, and approvals pass.

### Evidence Requirements <!-- wop:field evidence_requirements -->

- <Evidence.>

### Parallelism Rationale <!-- wop:field parallelism_rationale -->

<Independence or single-item reason.>

### Ownership Boundaries <!-- wop:field ownership_boundaries -->

<Boundaries.>

### Wave Execution Instructions <!-- wop:field execution_instructions -->

Execute only I003 in W003 after predecessor verification. Apply its ownership, final checks, and restrictions.

### Integration and Handoff <!-- wop:field integration_handoff -->

<Final handoff.>

#### Item I003 — <Name> <!-- wop:item I003 -->

##### Objective <!-- wop:field objective -->

<Objective.>

##### Context <!-- wop:field context -->

<Context.>

##### Inputs and Prerequisites <!-- wop:field inputs_prerequisites -->

- <Accepted W002 outputs.>

##### Scope <!-- wop:field scope -->

- <Work.>

##### Ownership <!-- wop:field ownership -->

- <Boundary.>

##### Outputs <!-- wop:field outputs -->

- <Output.>

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- <Criteria.>

##### Restrictions <!-- wop:field restrictions -->

- <Restriction.>

##### Verification Evidence <!-- wop:field verification_evidence -->

- <Evidence.>

##### Handoff Requirements <!-- wop:field handoff_requirements -->

- <Handoff.>

## Requirement Traceability <!-- wop:section requirement_traceability -->

| Requirement | Source | Items | Outputs | Verification | Final impact |
|---|---|---|---|---|---|
| R001 | <source> | I001-I003 | <outputs> | <evidence> | <impact> |

## Dependency Map <!-- wop:section dependency_map -->

| From | To | Type | Contract/output | Gate |
|---|---|---|---|---|
| W001 | W002 | <type> | <dependency> | <evidence> |

## Verification Strategy <!-- wop:section verification_strategy -->

<Test levels, environments, data, security, performance, document, operational, and end-to-end verification.>

## Rollback and Recovery <!-- wop:section rollback_recovery -->

<Triggers, owner, procedure, preserved data, and verification.>

## Final Acceptance <!-- wop:section final_acceptance -->

- <Outcome criterion, approving authority, and evidence.>

## Execution Protocol <!-- wop:section execution_protocol -->

Identify the package and read `README.md` plus every referenced wave prompt. Preserve the strict wave barrier, integrate all item results, and evaluate each completion gate before advancing. Parallelize only proven independent items. Stop on failed gates, unapproved external effects, or material scope changes. Record evidence and status transitions, then perform final acceptance.

## Revision History <!-- wop:section revision_history -->

- Version 1 — <timestamp> — Initial plan — <source>.
