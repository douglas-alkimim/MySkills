# Versioning

plan_id is a stable canonical lowercase UUID. Version is a positive integer for content revisions. created_at remains fixed; updated_at records the latest editorial content update using ISO 8601 with offset. Status projection, archive, restore, and administrative rename do not change updated_at.

Package directory names are current filenames, not identity. A content revision increments version and renames the directory to a new local timestamp. Administrative operations may change status, path, or events without incrementing content version.

Each generated prompt carries plan_id, plan_version, language, and source_readme_sha256. A hash mismatch is stale even when visible headings appear unchanged.

Revision records capture version, timestamp, summary, source, prior directory, and current directory. Revision history in README explains content decisions; SQLite revision rows provide operational audit. Keep both consistent without duplicating the complete diff.
