# Example: Fully Specified Simple Task

Request: “Add a verified CONTRIBUTING.md using the repository’s existing commands and do not change code.”

The request has a bounded deliverable, discoverable repository facts, and explicit scope. WOP does not interview. It inspects the repository, records actual commands and conventions, and chooses compact depth.

One wave is sufficient when a single item owns CONTRIBUTING.md:

- R001: document the verified setup, test, and contribution flow.
- I001 objective: create CONTRIBUTING.md from inspected project evidence.
- Ownership: CONTRIBUTING.md only.
- Acceptance: every documented command exists and was checked in the applicable environment; no source file changed; rendered Markdown is readable.
- Evidence: file diff plus actual command/help results.

If command discovery and document writing are assigned to different agents, they cannot share one wave because writing consumes discovery output. Use W001 discovery and W002 writing.

## Same outcome at three planning depths

The words “add CONTRIBUTING.md” do not determine complexity; the surrounding consequences do.

| Level | Task context | Plan and audit depth |
|---|---|---|
| Compact | One repository, one owned file, known commands, reversible change | One wave, one item, direct `R001 → I001 → file diff/command evidence`, Essential audit, concise pass summary |
| Standard | Several contributor guides and generated references must stay synchronized across packages | Multiple deliverables, explicit contracts/dependencies/integration, traceability matrix, Complete audit |
| Extensive | The contribution process spans regulated repositories, external identity systems, approval authorities, irreversible publication, and multiple agents | Stakeholders, risk, environments, isolation, rollback/recovery, full traceability, Detailed audit evidence |

All three retain language, metadata, objectives, acceptance criteria, strict sequencing, prompt consistency, final acceptance, and workspace integrity. Additional documentation exists only because the task context creates additional execution behavior or risk.

Before splitting any version, ask whether the split creates genuinely independent execution, improves verification, or reduces risk. Minor actions such as opening the template, editing prose, checking links, and reviewing the diff remain one cohesive item unless a real dependency or ownership boundary says otherwise.
