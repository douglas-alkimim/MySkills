# Adaptive Planning

Use the lightest planning level that safely covers the task. Planning depth follows actual consequences and coordination needs, not prompt length or a desire to make the plan appear sophisticated.

## Selection factors

Assess:

- risk and uncertainty;
- number of dependencies and deliverables;
- external effects and reversibility;
- coordination overhead;
- number of involved systems;
- need for multiple agents or disciplines.

A high-consequence dimension may justify Extensive even for a short request. A long request remains Compact or Standard when its work is bounded, low risk, and easy to reverse. The agent selects the level unless the choice materially changes the deliverable and requires user direction.

## Compact

Use for low-risk, bounded work with few deliverables, little uncertainty, and no complex dependency chain. A one-wave, one-item plan is valid and preferred when it completely represents the work. Keep metadata, outcome, relevant context, the wave/item objectives and criteria, direct requirement coverage, prompts, verification, final acceptance, and revision history. Add inputs, ownership, restrictions, dependencies, evidence procedures, risks, or recovery only when they change execution.

Omit irrelevant sections instead of writing filler such as “no risks,” “no dependencies,” or “no assumptions.” Compact is not a weakened Standard plan; it is a complete plan with fewer relevant concerns.

## Standard

Use for ordinary multi-deliverable projects with moderate scope, several dependencies, meaningful integration, or coordination. This is the default. Preserve complete requirements, contracts, wave/item specifications, traceability, dependency and integration information, verification, acceptance, execution protocol, and revision history. Include facts, assumptions, unknowns, decisions, and constraints when they affect execution; do not duplicate them across sections.

## Extensive

Use for high-risk or difficult-to-reverse work, large projects, multiple systems or disciplines, regulatory or security sensitivity, significant uncertainty, complex external effects, long critical paths, or difficult multi-agent coordination. Add the applicable stakeholder, risk, environment, operational, rollback, recovery, detailed contract, and expanded traceability controls. Extensive is never the default merely because the request is long.

## Reassessment

Increase planning depth when investigation reveals additional risk, uncertainty, dependencies, external effects, or coordination. Reduce unnecessary detail when evidence shows the task is simpler than expected, while preserving already relevant facts and controls. Never expand a simple task merely to fill a template.

## Proportional audit depth

Audit depth changes; correctness does not.

| Audit | Compact | Standard | Extensive |
|---|---|---|---|
| Planning | Essential | Complete | Detailed |
| Independence | When multiple items coexist | Pairwise | Pairwise with isolation analysis |
| Coverage | Direct verification | Traceability matrix | Full traceability |
| Writing | Essential | Complete | Complete |
| Risk | When relevant | Domain-dependent | Detailed |
| Recovery | When relevant | Risk-dependent | Detailed when applicable |
| Final acceptance | Mandatory | Mandatory | Mandatory |
| Workspace integrity | Mandatory | Mandatory | Mandatory |

Every level still verifies language, metadata, item and wave objectives and acceptance criteria, strict sequencing, same-wave independence when applicable, prompt existence and consistency, relevant SQLite/filesystem integrity, and final acceptance. A simple passing plan needs only a concise validation summary. Detailed audit evidence is appropriate when complexity or findings justify it.

## Anti-fragmentation test

WOP optimizes useful independent work, not the number of waves, items, or agents. Before splitting, ask: “Does splitting this work create genuinely independent execution, improve verification, or reduce risk?” If not, keep it together. A plan may contain one wave; a wave may contain one item. Separate work only for a real prerequisite, interference conflict, independently useful deliverable, verification boundary, or material risk control.
