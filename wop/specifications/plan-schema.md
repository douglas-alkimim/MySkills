# Plan Schema

README.md is UTF-8 Markdown with simple scalar YAML front matter.

## Required metadata

| Field | Rule |
|---|---|
| plan_id | Canonical lowercase UUID; stable for the plan’s lifetime. |
| title | Human-readable title. |
| version | Positive integer. |
| language | Any structurally valid BCP 47-style tag such as en, pt-BR, zh-CN, ar, or x-klingon; no closed registry is used. |
| complexity | compact, standard, or extensive. |
| plan_status | SQLite-authoritative value from status-model.md, projected here. |
| execution_status | SQLite-authoritative value from status-model.md, projected here. |
| acceptance_status | SQLite-authoritative value from status-model.md, projected here. |
| created_at | ISO 8601 timestamp with offset. |
| updated_at | ISO 8601 timestamp with offset. |

## Required sections

All plans require Outcome, Wave Sequence, one or more Wave sections, Verification Strategy, Final Acceptance, Execution Protocol, and Revision History.

Compact adds only context, constraints, dependencies, ownership, inputs, restrictions, risks, recovery, and separate traceability structures that materially affect execution. Direct mappings from outcome or requirements to items, outputs, checks, and final acceptance are valid. Empty-state filler is invalid planning practice even when mechanically parseable.

Standard additionally requires Execution Context, Requirements, and Requirement Traceability; a Dependency Map is required when multiple waves create dependencies. Confirmed Facts, Assumptions, Unknowns, Global Contracts, Scope, Constraints, Decisions, Risks, Environments, and Rollback are included when relevant. Extensive retains the complete structural section set and normally carries the applicable deeper stakeholder, risk, operational, rollback, recovery, and full-traceability structures.

## Parseable structure

Visible headings may use the plan language. Add stable hidden markers so semantics do not depend on their wording:

    ## Onda W001 — Nome <!-- wop:wave W001 -->
    ### Objetivo Geral <!-- wop:field general_objective -->
    ### Pré-requisitos <!-- wop:field prerequisites -->
    ### Requisitos Atendidos <!-- wop:field requirements_addressed -->
    ### Critérios Gerais de Aceite <!-- wop:field general_acceptance_criteria -->
    ### Gate de Conclusão <!-- wop:field completion_gate -->
    ### Requisitos de Evidência <!-- wop:field evidence_requirements -->
    ### Justificativa de Paralelismo <!-- wop:field parallelism_rationale -->
    ### Limites de Propriedade <!-- wop:field ownership_boundaries -->
    ### Instruções de Execução da Onda <!-- wop:field execution_instructions -->
    ### Integração e Handoff <!-- wop:field integration_handoff -->

Each item uses:

    #### Item I001 — Nome <!-- wop:item I001 -->
    ##### Objetivo <!-- wop:field objective -->
    ##### Contexto <!-- wop:field context -->
    ##### Entradas e Pré-requisitos <!-- wop:field inputs_prerequisites -->
    ##### Escopo <!-- wop:field scope -->
    ##### Responsabilidade <!-- wop:field ownership -->
    ##### Saídas <!-- wop:field outputs -->
    ##### Critérios de Aceite <!-- wop:field acceptance_criteria -->
    ##### Restrições <!-- wop:field restrictions -->
    ##### Evidências de Verificação <!-- wop:field verification_evidence -->
    ##### Requisitos de Handoff <!-- wop:field handoff_requirements -->

For Compact, the mandatory wave fields are `general_objective`, `general_acceptance_criteria`, and `completion_gate`; the mandatory item fields are `objective`, `scope`, `outputs`, and `acceptance_criteria`. Add the remaining fields whenever needed for correct execution. A multi-item Compact wave must add `parallelism_rationale`, `ownership_boundaries`, and item ownership so independence is auditable. Standard and Extensive retain the complete field sets shown above. Every new plan should include wave `execution_instructions`; legacy omission remains a compatibility warning.

Plan-level sections use `<!-- wop:section section_id -->`. A custom section is global by default. Narrow it with `scope=wave waves=W002,W003` or `scope=item items=I004,I005`; selectors must resolve to existing IDs. Wave IDs are sequential from W001. Item IDs are unique across the plan. Markers are the universal mechanism for every language and custom heading. Legacy English, Portuguese, and Spanish headings remain recognized without markers only as a compatibility aid. Existing waves without `execution_instructions` remain readable, but new or revised plans should state this field explicitly. See plan-ir.md for IDs, scope, compatibility, and generation behavior.
