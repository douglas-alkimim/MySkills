# Database Schema

Database location: PROJECT/.wop/wop.sqlite3. Foreign keys are enabled on every connection. All mutations use transactions and parameterized SQL.

## plans

Primary key plan_id. Stores title, unique current directory name and relative path, created and updated timestamps, version, language, complexity, independent plan/execution/acceptance statuses, pre-archive status, archived_at, package content hash, prompt integrity status, and observed artifact integrity (`valid`, `invalid`, `unchecked`, `missing`, or `conflict`).

## plan_relations

Composite primary key over source, target, and type. Both IDs reference plans with restricted deletion. Self-relations are forbidden. Types: depends_on, related_to, supersedes, derived_from.

`depends_on` is directed and must remain acyclic. Other relationship types do not participate in the dependency graph. `check` audits legacy or externally introduced cycles.

## plan_revisions

UUID revision_id, plan_id foreign key, version, timestamp, summary, source, previous directory name, and current directory name.

## plan_events

UUID event_id, stable plan_id, event_type, timestamp, and JSON details. It deliberately retains deletion events after the plans row is removed.

## plan_tombstones

Primary key plan_id plus deletion time, previous directory, and reason. Tombstones prevent ID reuse.

## plan_evidence

UUID evidence_id, stable plan_id, evidence type (`execution`, `acceptance`, or both), artifact/report/log reference, summary, identifiable actor, human-approval flag, and timestamp. It stores produced-evidence references rather than planned evidence text.

## plan_operations

UUID operation_id, optional plan_id, operation type, source and target paths, start/end timestamps, state (`pending`, `completed`, `rolled_back`, or `failed`), and JSON recovery details. It makes cross-filesystem/database operations observable without claiming joint transactional atomicity.

Indexes cover titles, each status dimension, relation targets, plan revisions, and plan events. CHECK constraints enforce status, relation, complexity, integrity-status, and positive-version enums. See scripts/wop_db.py for the executable schema.
