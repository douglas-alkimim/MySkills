# Plan Relationships

Supported directed relations:

- depends_on: source cannot complete without target.
- related_to: source and target share relevant scope without a prerequisite.
- supersedes: source replaces target for stated scope.
- derived_from: source was created from target evidence or structure.

Create a relation with:

    python SKILL/scripts/wop_db.py --root PROJECT relate \
      --source-id UUID --target-id UUID --type TYPE --rationale TEXT

Inspect both incoming and outgoing relations:

    python SKILL/scripts/wop_db.py --root PROJECT relations --id UUID

Every relation requires a rationale. Self-relations and references to unregistered plans are invalid. A new `depends_on` relation is rejected if it introduces a directed cycle; `check` also reports preexisting cycles. `related_to`, `supersedes`, and `derived_from` do not participate in dependency-cycle detection. Before archive, revision, consolidation, or delete, inspect relationships and explain downstream consequences. Never delete dependent plans automatically.
