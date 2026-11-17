# Discover and Read

Use SQLite first:

    python SKILL/scripts/wop_db.py --root PROJECT list
    python SKILL/scripts/wop_db.py --root PROJECT search --query TEXT
    python SKILL/scripts/wop_db.py --root PROJECT get --id UUID
    python SKILL/scripts/wop_db.py --root PROJECT get --name DIRECTORY

List excludes archived plans by default; add --include-archived when needed. Search covers stable ID, title, current directory name, status fields, and readable README content.

Verify the indexed package exists before relying on it. For READ, open the complete README and relevant prompts without modification. Read all prompts when evaluating orchestration or synchronization; read only relevant waves for targeted factual questions.

If the index and filesystem disagree, report the inconsistency and use check. Do not silently repair during a read-only request.
