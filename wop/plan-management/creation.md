# Create

1. Initialize the workspace.
2. List and search existing plans. Decide whether the request is new, a revision, or related work.
3. Understand, inspect, and clarify using core/planning-process.md.
4. Select compact, standard, or extensive depth from actual risk, uncertainty, dependencies, deliverables, external effects, reversibility, systems, and coordination. Use the lightest safe level; one wave and one item are valid.
5. Create a stable UUID and timestamped package under .wop/plans.
6. Write the complete README from the matching template. Omit irrelevant optional Compact content instead of filling empty sections. Keep the global execution protocol item-agnostic, add wave-specific execution instructions, and scope every custom section explicitly when it is not global.
7. Apply proportional audit depth from core/adaptive-planning.md. Universal invariants, relevant same-wave independence, final acceptance, and workspace integrity remain mandatory.
8. Generate prompts and validate:

       python SKILL/scripts/validate_plan.py --root PROJECT \
         --directory PACKAGE --generate-prompts

9. Review the listed semantic checks. Fix and regenerate until both mechanical and semantic checks pass.
10. Register:

       python SKILL/scripts/wop_db.py --root PROJECT \
         register --directory PACKAGE

Set plan_status ready only when all artifacts and audits pass. Otherwise keep draft and report exact defects. Registration refuses duplicate or tombstoned IDs.
