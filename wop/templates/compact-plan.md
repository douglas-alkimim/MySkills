---
plan_id: <canonical-lowercase-uuid>
title: <plan-title>
version: 1
language: <language-tag>
complexity: compact
plan_status: draft
execution_status: not_started
acceptance_status: not_evaluated
created_at: <iso-8601-with-offset>
updated_at: <iso-8601-with-offset>
---

# <Plan Title>

<!-- Keep only information that changes execution. Omit irrelevant optional sections and fields instead of filling them with "none" statements. -->

## Outcome and Deliverables <!-- wop:section outcome -->

- R001: <Observable result and deliverable.>

## Relevant Context and Constraints <!-- wop:section execution_context -->

<Only the facts, boundaries, paths, compatibility needs, or constraints required to execute the work.>

## Wave Sequence <!-- wop:section wave_sequence -->

1. W001 — <Name and result>.

## Wave W001 — <Name> <!-- wop:wave W001 -->

### General Objective <!-- wop:field general_objective -->

<Wave result.>

### General Acceptance Criteria <!-- wop:field general_acceptance_criteria -->

- <Observable wave pass condition.>

### Completion Gate <!-- wop:field completion_gate -->

I001 is accepted with evidence and the general criterion passes.

### Wave Execution Instructions <!-- wop:field execution_instructions -->

Execute only I001 in W001. Do not expand the scope or create additional work units without a concrete dependency, verification, or risk benefit.

#### Item I001 — <Name> <!-- wop:item I001 -->

##### Objective <!-- wop:field objective -->

<One bounded result.>

##### Scope <!-- wop:field scope -->

- <Required work.>

##### Outputs <!-- wop:field outputs -->

- <Deliverable and location.>

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- <Expected state, observation method, and pass threshold.>

## Verification and Final Checks <!-- wop:section verification_strategy -->

- R001 → I001: <Check, actual evidence to retain, and expected result.>

## Final Acceptance <!-- wop:section final_acceptance -->

- <Condition proving the requested outcome and deliverable.>

## Execution Protocol <!-- wop:section execution_protocol -->

Identify the package, read `README.md` and the referenced wave prompt, execute waves strictly in order, evaluate each completion gate from actual evidence, and perform final acceptance.

## Revision History <!-- wop:section revision_history -->

- Version 1 — <timestamp> — Initial plan.
