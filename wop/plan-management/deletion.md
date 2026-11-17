# Archive, Restore, and Delete

Archive preserves the complete package and identity:

    python SKILL/scripts/wop_db.py --root PROJECT archive --id UUID

Restore moves it back to plans, refuses collisions, preserves history, and restores the pre-archive plan status:

    python SKILL/scripts/wop_db.py --root PROJECT restore --id UUID

Archive is not deletion and is not automatic after execution or acceptance.

Permanent delete requires explicit user confirmation of the exact plan. Before invoking it:

1. resolve stable ID and current package;
2. inspect incoming and outgoing relationships;
3. explain loss of the package and retained audit metadata;
4. refuse to cascade to dependent plans;
5. obtain confirmation;
6. invoke:

       python SKILL/scripts/wop_db.py --root PROJECT \
         delete --id UUID --confirm --reason TEXT

The command stages the package under a recovery name, commits database deletion plus tombstone/event, restores the package if the database step fails, then removes the staged package. A tombstoned ID cannot be registered again.
