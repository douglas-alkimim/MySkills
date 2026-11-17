# Acceptance Criteria

Criteria define observable truth, not activity.

## Strong criterion

A strong criterion names the expected state, how it is observed, and the pass condition. Include commands or procedures when known. Distinguish evidence produced during execution from evidence the planner actually observed.

Avoid “implemented,” “works,” “looks good,” “tested,” or “complete” without a measurable condition. Do not require a specific command when the environment is unknown; state the invariant and an acceptable verification class.

## Logical hierarchy

Item criteria prove item outputs. Integration checks prove outputs coexist. The conjunction of item and integration criteria must imply the wave criteria. The conjunction of all wave gates and final checks must imply final acceptance.

## Evidence

Evidence may be test output, rendered inspection, schema query, checksum, benchmark, log, review record, or reproducible manual procedure. Record command/procedure, environment, result, and any limitation. A claim without evidence remains unaccepted.

Acceptance status is independent of execution status. Executed work can be pending or rejected; completed implementation does not automatically establish user acceptance.
