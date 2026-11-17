# Writing for Agents

Write instructions that change execution behavior.

## Standards

- Lead with the objective and completion condition.
- Name inputs, outputs, ownership, restrictions, evidence, and handoff.
- Put shared contracts in one authoritative plan section; copy only execution-critical excerpts into standalone prompts.
- Use stable identifiers and consistent terms.
- Separate fact, decision, assumption, unknown, and requirement.
- Prefer observable criteria to adjectives.
- Preserve necessary context; remove generic explanation and repeated guidance.
- Place specialist detail behind explicit routing links.

Apply the no-op test sentence by sentence: if deletion would not change a capable agent’s decision or result, delete it. Do not optimize for shortness at the expense of a missing contract, risk, or criterion.

Completion criteria cause the necessary work. A precise done condition is more valuable than several paragraphs of encouragement.
