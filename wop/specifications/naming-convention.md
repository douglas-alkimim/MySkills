# Naming Convention

Package directory:

    YYYY_MM_DD_hh_mm_ss-name_snake_case

Use local time for the filename timestamp and store the offset in metadata timestamps. name contains lowercase ASCII letters, digits, and underscores, starts and ends with an alphanumeric character, and describes the plan rather than a transient status.

Files:

- README.md is the authoritative plan.
- prompts/wave-01.md, wave-02.md, and so on correspond to wave order.
- prompts/execute-all.md is the master orchestration prompt.

Identifiers:

- plan_id: canonical lowercase UUID.
- requirements: R001, R002, sequential and stable where possible.
- waves: W001, W002, sequential.
- items: I001, I002, unique across the plan.
- decisions may use D001 when explicit tracking adds value.

Technical identifiers and filenames remain English even when plan prose uses another language.
