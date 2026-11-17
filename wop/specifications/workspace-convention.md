# Workspace Convention

The correct project root is the narrowest durable root containing the artifacts the plan governs and from which execution paths can be resolved. Do not create nested .wop directories for the same project.

The required layout is:

    PROJECT/.wop/wop.sqlite3
    PROJECT/.wop/plans/PACKAGE/README.md
    PROJECT/.wop/plans/PACKAGE/prompts/wave-NN.md
    PROJECT/.wop/plans/PACKAGE/prompts/execute-all.md
    PROJECT/.wop/archive/PACKAGE/...

plans contains active packages regardless of execution or acceptance. archive contains preserved archived, cancelled, or superseded packages. Do not auto-archive after execution.

Packages are direct children of plans or archive. Lifecycle scripts resolve paths and reject deeper, traversed, or external targets before mutation. SQLite never stores plan body content; it stores operational metadata and relative paths.

Lifecycle commands record cross-resource work in `plan_operations`. A `pending` or `failed` operation is never a passing audit result. Follow the exact source/target paths and recovery details reported by `check`; do not discard either filesystem or database evidence during reconciliation.
