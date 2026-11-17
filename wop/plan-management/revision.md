# Update and Consolidate

## Update

Preserve plan_id and created_at. For any content change:

1. Identify affected requirements, contracts, waves, items, relations, and prompts.
2. Increment version and update updated_at.
3. Apply the change to authoritative README.md and revision history.
4. Regenerate all prompts atomically; the generator removes stale extra wave prompts.
5. Revalidate mechanically and semantically.
6. Rename the package with a current local timestamp using `wop_db.py rename`. This controlled operation verifies the exact version increment, changed updated_at, generated prompts, stable identity, and then updates SQLite plus revision history with rollback on failure.
7. Run `wop_db.py check` and verify path, version, hash, prompt integrity, and the new revision record. Do not use rebuild as an ordinary revision operation.

Do not leave derivative prompts from a previous README hash.

## Consolidate

Create a new plan unless the user explicitly chooses one source identity as authoritative. Preserve source IDs with derived_from, related_to, or supersedes relations. Compare requirements and contracts, surface contradictions, choose resolutions explicitly, retain traceability to sources, and do not silently discard scope. Consolidation does not delete or archive sources automatically.
