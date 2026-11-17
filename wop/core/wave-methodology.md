# Wave Methodology

A wave is a concurrency boundary and an acceptance unit.

WOP optimizes useful independent work, not the number of waves, items, or agents. A plan may contain one wave, and a wave may contain one item. Do not create artificial waves or turn every minor action into an item. Keep cohesive work together when the resulting fragments would still require continuous coordination.

## Hard barrier

Wave N+1 cannot start until every item in Wave N:

1. finishes its owned scope;
2. passes its item criteria with evidence;
3. integrates where necessary;
4. satisfies its handoff contract; and
5. contributes to a passing general wave gate.

Partial progression is invalid. A completed item may wait, but it cannot authorize downstream work by itself.

## Required wave specification

Every wave defines ID, name, general objective, general acceptance criteria, and completion gate. Add prerequisites, requirements addressed, evidence, parallelism rationale, ownership boundaries, and integration/handoff whenever they affect execution; Standard and Extensive normally use the complete set. New plans include wave-specific execution instructions that name only the current wave's items and never release a later wave.

For a multi-item wave, compare every pair. State why their inputs are available, outputs are distinct, mutable resources do not overlap, decisions do not depend on each other, and integration does not require mid-wave coordination.

Subdivide an item only when the subdivision creates meaningful independent work, improves verification, or reduces execution risk. Prefer clear ownership and meaningful deliverables over arbitrary counts. Dependent work remains together unless an actual prerequisite or conflict requires another wave.

## Required item specification

Every item defines ID, name, objective, scope, outputs, and acceptance criteria. Add context, inputs and prerequisites, ownership, restrictions, verification evidence, and handoff whenever necessary; Standard and Extensive normally use the complete set. Multi-item waves always need auditable ownership and independence detail.

## Construction test

- The union of item objectives covers the wave objective.
- All item criteria plus integration checks logically imply the general wave criteria.
- Every predecessor output consumed by the wave is named and gated.
- No item changes another item’s owned artifact or shared resource without proven isolation.
- Moving an item earlier would not violate a dependency; moving it later would not improve safety enough to justify lost parallelism.
- Splitting the work creates a concrete independence, verification, or risk benefit greater than its coordination overhead; otherwise keep one item.
