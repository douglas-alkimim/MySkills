# Workspace

Each project has one .wop directory at the correct project root:

    .wop/
      wop.sqlite3
      plans/
        YYYY_MM_DD_hh_mm_ss-plan_name/
          README.md
          prompts/
            wave-01.md
            execute-all.md
      archive/

Use an explicit project root:

    python SKILL/scripts/init_workspace.py --root PROJECT

Initialization creates missing directories and schema objects, enables foreign keys, checks database integrity, and never overwrites plan data.

Directory timestamps use local time; plan metadata stores ISO 8601 timestamps with an offset. Package names use snake_case after the timestamp. The timestamp changes on content revision; plan_id never changes.

README.md is authoritative for objectives, requirements, waves, items, criteria, contracts, and editorial revision history. `prompts/` is authoritative for generated execution instructions and contains one standalone prompt per wave plus execute-all.md. SQLite is authoritative for stable identity, current name/path, administrative, execution and acceptance states, produced-evidence references, relations, operations, revisions, events, and tombstones. README status fields are synchronized projections only. Do not place secrets, execution artifacts, test workspaces, or unrelated project state in .wop.

Run wop_db.py --root PROJECT check to detect missing packages, unindexed packages, path or metadata disagreement, invalid/unchecked prompts, hash mismatch, archive-state mismatch, unfinished operations, dependency cycles, relationship faults, and tombstone reuse. Use rebuild only after reviewing ambiguous packages. Rebuild preserves existing SQLite operational states and history; a stale README projection is a reported conflict, not permission to overwrite indexed state.
