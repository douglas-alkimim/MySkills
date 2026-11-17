#!/usr/bin/env python3
"""SQLite index and recoverable lifecycle operations for WOP plan packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence, Tuple, Union


PLAN_STATUSES = (
    "draft", "ready", "in_progress", "blocked", "completed",
    "accepted", "cancelled", "superseded", "archived",
)
EXECUTION_STATUSES = (
    "not_started", "in_progress", "partially_executed",
    "blocked", "executed", "abandoned",
)
ACCEPTANCE_STATUSES = ("not_evaluated", "pending", "accepted", "rejected")
COMPLEXITIES = ("compact", "standard", "extensive")
RELATION_TYPES = ("depends_on", "related_to", "supersedes", "derived_from")
INTEGRITY_STATUSES = ("valid", "invalid", "unchecked", "missing", "conflict")
PACKAGE_PATTERN = re.compile(
    r"^\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}-[a-z0-9]+(?:_[a-z0-9]+)*$"
)


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS plans (
    plan_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    current_directory_name TEXT NOT NULL UNIQUE,
    current_relative_path TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL CHECK(version >= 1),
    language TEXT NOT NULL,
    complexity TEXT NOT NULL CHECK(complexity IN ('compact','standard','extensive')),
    plan_status TEXT NOT NULL CHECK(plan_status IN
        ('draft','ready','in_progress','blocked','completed','accepted',
         'cancelled','superseded','archived')),
    execution_status TEXT NOT NULL CHECK(execution_status IN
        ('not_started','in_progress','partially_executed','blocked','executed','abandoned')),
    acceptance_status TEXT NOT NULL CHECK(acceptance_status IN
        ('not_evaluated','pending','accepted','rejected')),
    archived_at TEXT,
    pre_archive_plan_status TEXT CHECK(
        pre_archive_plan_status IS NULL OR pre_archive_plan_status IN
        ('draft','ready','in_progress','blocked','completed','accepted',
         'cancelled','superseded')),
    content_hash TEXT NOT NULL,
    prompt_integrity_status TEXT NOT NULL CHECK(prompt_integrity_status IN
        ('valid','invalid','unchecked')),
    artifact_integrity_status TEXT NOT NULL DEFAULT 'unchecked' CHECK(
        artifact_integrity_status IN
        ('valid','invalid','unchecked','missing','conflict'))
);

CREATE TABLE IF NOT EXISTS plan_relations (
    source_plan_id TEXT NOT NULL,
    target_plan_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK(relation_type IN
        ('depends_on','related_to','supersedes','derived_from')),
    rationale TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY(source_plan_id, target_plan_id, relation_type),
    CHECK(source_plan_id <> target_plan_id),
    FOREIGN KEY(source_plan_id) REFERENCES plans(plan_id) ON DELETE RESTRICT,
    FOREIGN KEY(target_plan_id) REFERENCES plans(plan_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS plan_revisions (
    revision_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    version INTEGER NOT NULL CHECK(version >= 1),
    timestamp TEXT NOT NULL,
    summary TEXT NOT NULL,
    source TEXT NOT NULL,
    previous_directory_name TEXT,
    current_directory_name TEXT NOT NULL,
    FOREIGN KEY(plan_id) REFERENCES plans(plan_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS plan_events (
    event_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    details TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plan_tombstones (
    plan_id TEXT PRIMARY KEY,
    deleted_at TEXT NOT NULL,
    previous_directory_name TEXT NOT NULL,
    deletion_reason TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plan_evidence (
    evidence_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL CHECK(evidence_type IN
        ('execution','acceptance','execution_and_acceptance')),
    reference TEXT NOT NULL,
    summary TEXT NOT NULL,
    actor TEXT NOT NULL,
    human_approved INTEGER NOT NULL DEFAULT 0 CHECK(human_approved IN (0,1)),
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plan_operations (
    operation_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN
        ('pending','completed','rolled_back','failed')),
    started_at TEXT NOT NULL,
    completed_at TEXT,
    source_path TEXT,
    target_path TEXT,
    details TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_plans_title ON plans(title);
CREATE INDEX IF NOT EXISTS idx_plans_plan_status ON plans(plan_status);
CREATE INDEX IF NOT EXISTS idx_plans_execution_status ON plans(execution_status);
CREATE INDEX IF NOT EXISTS idx_plans_acceptance_status ON plans(acceptance_status);
CREATE INDEX IF NOT EXISTS idx_relations_target ON plan_relations(target_plan_id);
CREATE INDEX IF NOT EXISTS idx_revisions_plan ON plan_revisions(plan_id, version);
CREATE INDEX IF NOT EXISTS idx_events_plan ON plan_events(plan_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_evidence_plan ON plan_evidence(plan_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_operations_plan ON plan_operations(plan_id, started_at);
"""


class WopError(RuntimeError):
    """An expected user-facing WOP failure."""


class ClosingConnection(sqlite3.Connection):
    """Commit or roll back, then release the SQLite file on every context exit."""

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        suppress = super().__exit__(exc_type, exc, traceback)
        self.close()
        return suppress


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def workspace(root: Path) -> Path:
    return root.resolve() / ".wop"


def database_path(root: Path) -> Path:
    return workspace(root) / "wop.sqlite3"


def connect(root: Path, require_existing: bool = True) -> sqlite3.Connection:
    db = database_path(root)
    if require_existing and not db.exists():
        raise WopError(
            "WOP database does not exist: {0}. Run init_workspace.py first.".format(db)
        )
    conn = sqlite3.connect(str(db), factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_column(
    conn: sqlite3.Connection, table: str, column: str, declaration: str
) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info({0})".format(table))}
    if column not in columns:
        conn.execute(
            "ALTER TABLE {0} ADD COLUMN {1} {2}".format(table, column, declaration)
        )


def initialize(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.exists() or not root.is_dir():
        raise WopError("Project root is not a directory: {0}".format(root))
    wop = workspace(root)
    (wop / "plans").mkdir(parents=True, exist_ok=True)
    (wop / "archive").mkdir(parents=True, exist_ok=True)
    with connect(root, require_existing=False) as conn:
        conn.executescript(SCHEMA)
        _ensure_column(
            conn,
            "plans",
            "pre_archive_plan_status",
            "TEXT CHECK(pre_archive_plan_status IS NULL OR "
            "pre_archive_plan_status IN ('draft','ready','in_progress','blocked',"
            "'completed','accepted','cancelled','superseded'))",
        )
        _ensure_column(
            conn,
            "plans",
            "artifact_integrity_status",
            "TEXT NOT NULL DEFAULT 'unchecked' CHECK(artifact_integrity_status IN "
            "('valid','invalid','unchecked','missing','conflict'))",
        )
        foreign_keys = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    return {
        "workspace": str(wop),
        "database": str(database_path(root)),
        "foreign_keys": bool(foreign_keys),
        "integrity": integrity,
    }


def parse_frontmatter(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise WopError("Missing plan README: {0}".format(path))
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise WopError("Missing YAML front matter: {0}".format(path))
    data: dict[str, str] = {}
    closed = False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise WopError(
                "Unsupported front matter line in {0}: {1}".format(path, line)
            )
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    if not closed:
        raise WopError("Unclosed YAML front matter: {0}".format(path))
    return data


def _write_utf8_atomic(path: Path, text: str) -> None:
    temp = path.with_name(".{0}.{1}.tmp".format(path.name, uuid.uuid4().hex))
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temp), str(path))
    finally:
        if temp.exists():
            temp.unlink()


def update_frontmatter_projection(
    package: Path, updates: dict[str, str]
) -> bytes:
    readme = package / "README.md"
    original = readme.read_bytes()
    text = original.decode("utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise WopError("README has no front matter: {0}".format(readme))
    closing = None
    found: set[str] = set()
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing = index
            break
        if ":" not in lines[index]:
            continue
        key = lines[index].split(":", 1)[0].strip()
        if key in updates:
            lines[index] = "{0}: {1}".format(key, updates[key])
            found.add(key)
    if closing is None:
        raise WopError("README front matter is not closed: {0}".format(readme))
    missing = set(updates) - found
    if missing:
        insertion = ["{0}: {1}".format(key, updates[key]) for key in sorted(missing)]
        lines[closing:closing] = insertion
    _write_utf8_atomic(readme, "\n".join(lines) + "\n")
    return original


def restore_readme(package: Path, original: bytes) -> None:
    readme = package / "README.md"
    temp = readme.with_name(".{0}.{1}.restore".format(readme.name, uuid.uuid4().hex))
    try:
        temp.write_bytes(original)
        os.replace(str(temp), str(readme))
    finally:
        if temp.exists():
            temp.unlink()


def content_hash(package: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        path for path in package.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in (".pyc", ".sqlite3")
        and not path.name.startswith(".generate-")
    )
    for path in files:
        digest.update(path.relative_to(package).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def validate_uuid(value: str) -> str:
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise WopError("Invalid plan UUID: {0}".format(value)) from exc
    if str(parsed) != value.lower():
        raise WopError("Plan UUID must use canonical lowercase form.")
    return value


def normalize_package(
    root: Path, value: Union[str, Path], must_exist: bool = True
) -> Path:
    root = root.resolve()
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    allowed = [
        (workspace(root) / "plans").resolve(),
        (workspace(root) / "archive").resolve(),
    ]
    if not any(path.parent == candidate for candidate in allowed):
        raise WopError(
            "A plan package must be a direct child of .wop/plans or .wop/archive."
        )
    if must_exist and (not path.is_dir() or not (path / "README.md").is_file()):
        raise WopError("Plan package is missing or incomplete: {0}".format(path))
    if not PACKAGE_PATTERN.fullmatch(path.name):
        raise WopError("Invalid package directory name: {0}".format(path.name))
    return path


def relative_path(root: Path, package: Path) -> str:
    return package.resolve().relative_to(root.resolve()).as_posix()


def metadata_from_package(package: Path) -> dict[str, Any]:
    data = parse_frontmatter(package / "README.md")
    required = (
        "plan_id", "title", "version", "language", "complexity", "plan_status",
        "execution_status", "acceptance_status", "created_at", "updated_at",
    )
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise WopError("Missing plan metadata: {0}".format(", ".join(missing)))
    validate_uuid(data["plan_id"])
    try:
        version = int(data["version"])
    except ValueError as exc:
        raise WopError("Plan version must be an integer.") from exc
    if version < 1:
        raise WopError("Plan version must be at least 1.")
    if data["complexity"] not in COMPLEXITIES:
        raise WopError("Invalid complexity: {0}".format(data["complexity"]))
    if data["plan_status"] not in PLAN_STATUSES:
        raise WopError("Invalid plan status: {0}".format(data["plan_status"]))
    if data["execution_status"] not in EXECUTION_STATUSES:
        raise WopError("Invalid execution status: {0}".format(data["execution_status"]))
    if data["acceptance_status"] not in ACCEPTANCE_STATUSES:
        raise WopError("Invalid acceptance status: {0}".format(data["acceptance_status"]))
    return dict(data, version=version)


def prompt_integrity_detail(
    package: Path, root: Optional[Path] = None
) -> Tuple[str, str]:
    try:
        from validate_plan import validate_package
        report = validate_package(package, root=root, check_database=False)
    except Exception as exc:
        return "unchecked", "{0}: {1}".format(exc.__class__.__name__, exc)
    if report.get("valid"):
        return "valid", "All mechanical package checks passed."
    codes = {item.get("code", "") for item in report.get("errors", [])}
    if any(code.startswith("missing") or code == "execute_all" for code in codes):
        return "missing", "Required plan or prompt artifacts are missing."
    if any(
        code in (
            "prompt_metadata", "execute_all_metadata", "database_metadata",
            "database_path", "tombstone_reuse",
        )
        for code in codes
    ):
        return "conflict", "Plan artifacts disagree with their authoritative metadata."
    return "invalid", "Plan package validation reported errors."


def prompt_integrity(package: Path, root: Optional[Path] = None) -> str:
    return prompt_integrity_detail(package, root)[0]


def rows(rows_value: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows_value]


def add_event(
    conn: sqlite3.Connection, plan_id: str, event_type: str, details: dict[str, Any]
) -> None:
    conn.execute(
        "INSERT INTO plan_events(event_id,plan_id,event_type,timestamp,details) "
        "VALUES(?,?,?,?,?)",
        (
            str(uuid.uuid4()),
            plan_id,
            event_type,
            now(),
            json.dumps(details, sort_keys=True),
        ),
    )


def add_revision(
    conn: sqlite3.Connection,
    plan_id: str,
    version: int,
    summary: str,
    source: str,
    previous_name: Optional[str],
    current_name: str,
) -> None:
    conn.execute(
        "INSERT INTO plan_revisions(revision_id,plan_id,version,timestamp,summary,"
        "source,previous_directory_name,current_directory_name) VALUES(?,?,?,?,?,?,?,?)",
        (
            str(uuid.uuid4()), plan_id, version, now(), summary, source,
            previous_name, current_name,
        ),
    )


def start_operation(
    root: Path,
    plan_id: str,
    operation_type: str,
    source_path: Optional[Path] = None,
    target_path: Optional[Path] = None,
) -> str:
    operation_id = str(uuid.uuid4())
    with connect(root) as conn:
        conn.execute(
            "INSERT INTO plan_operations(operation_id,plan_id,operation_type,status,"
            "started_at,source_path,target_path,details) VALUES(?,?,?,?,?,?,?,?)",
            (
                operation_id,
                plan_id,
                operation_type,
                "pending",
                now(),
                str(source_path) if source_path else None,
                str(target_path) if target_path else None,
                "{}",
            ),
        )
    return operation_id


def finish_operation(
    root: Path, operation_id: str, status: str, details: dict[str, Any]
) -> None:
    if status not in ("completed", "rolled_back", "failed"):
        raise WopError("Invalid operation completion status: {0}".format(status))
    with connect(root) as conn:
        conn.execute(
            "UPDATE plan_operations SET status=?,completed_at=?,details=? "
            "WHERE operation_id=?",
            (status, now(), json.dumps(details, sort_keys=True), operation_id),
        )


def get_plan(
    root: Path, plan_id: Optional[str] = None, name: Optional[str] = None
) -> dict[str, Any]:
    if bool(plan_id) == bool(name):
        raise WopError("Provide exactly one of plan ID or directory name.")
    with connect(root) as conn:
        if plan_id:
            validate_uuid(plan_id)
            row = conn.execute("SELECT * FROM plans WHERE plan_id=?", (plan_id,)).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM plans WHERE current_directory_name=?", (name,)
            ).fetchone()
    if row is None:
        raise WopError("Plan was not found.")
    return dict(row)


def register(
    root: Path, directory: Union[str, Path], source: str = "register"
) -> dict[str, Any]:
    package = normalize_package(root, directory)
    meta = metadata_from_package(package)
    plan_id = meta["plan_id"]
    archived = package.parent.name == "archive"
    integrity, integrity_message = prompt_integrity_detail(package, root)
    requested_plan_status = meta["plan_status"]
    operational_plan_status = (
        "archived"
        if archived
        else requested_plan_status if requested_plan_status in ("draft", "ready") else "draft"
    )
    if operational_plan_status == "ready" and integrity != "valid":
        raise WopError(
            "A ready plan must pass validation; integrity is {0}: {1}".format(
                integrity, integrity_message
            )
        )
    projection_original: Optional[bytes] = None
    projection_required = (
        not archived
        and (
            meta["execution_status"] != "not_started"
            or meta["acceptance_status"] != "not_evaluated"
            or meta["plan_status"] != operational_plan_status
        )
    )
    if projection_required:
        projection_original = update_frontmatter_projection(
            package,
            {
                "plan_status": operational_plan_status,
                "execution_status": "not_started",
                "acceptance_status": "not_evaluated",
            },
        )
    record = (
        plan_id,
        meta["title"],
        package.name,
        relative_path(root, package),
        meta["created_at"],
        meta["updated_at"],
        meta["version"],
        meta["language"],
        meta["complexity"],
        operational_plan_status,
        "not_started",
        "not_evaluated",
        now() if archived else None,
        requested_plan_status if archived and requested_plan_status != "archived" else None,
        content_hash(package),
        integrity if integrity in ("valid", "invalid", "unchecked") else "invalid",
        integrity,
    )
    try:
        with connect(root) as conn:
            if conn.execute(
                "SELECT 1 FROM plan_tombstones WHERE plan_id=?", (plan_id,)
            ).fetchone():
                raise WopError(
                    "Plan ID is tombstoned and cannot be reused: {0}".format(plan_id)
                )
            if conn.execute("SELECT 1 FROM plans WHERE plan_id=?", (plan_id,)).fetchone():
                raise WopError("Plan is already registered: {0}".format(plan_id))
            conn.execute(
                "INSERT INTO plans(plan_id,title,current_directory_name,current_relative_path,"
                "created_at,updated_at,version,language,complexity,plan_status,"
                "execution_status,acceptance_status,archived_at,pre_archive_plan_status,"
                "content_hash,prompt_integrity_status,artifact_integrity_status) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                record,
            )
            add_revision(
                conn, plan_id, meta["version"], "Initial registration", source, None,
                package.name,
            )
            add_event(
                conn,
                plan_id,
                "registered",
                {
                    "path": relative_path(root, package),
                    "integrity": integrity,
                    "readme_execution_projection": meta["execution_status"],
                    "readme_acceptance_projection": meta["acceptance_status"],
                    "operational_execution_status": "not_started",
                    "operational_acceptance_status": "not_evaluated",
                },
            )
    except Exception:
        if projection_original is not None:
            restore_readme(package, projection_original)
        raise
    return get_plan(root, plan_id=plan_id)


def list_plans(
    root: Path,
    plan_status: Optional[str] = None,
    execution_status: Optional[str] = None,
    include_archived: bool = False,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[str] = []
    if plan_status:
        clauses.append("plan_status=?")
        params.append(plan_status)
    elif not include_archived:
        clauses.append("plan_status<>'archived'")
    if execution_status:
        clauses.append("execution_status=?")
        params.append(execution_status)
    sql = "SELECT * FROM plans"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY updated_at DESC,title"
    with connect(root) as conn:
        return rows(conn.execute(sql, params))


def search(root: Path, query: str, include_archived: bool = True) -> list[dict[str, Any]]:
    needle = query.casefold()
    sql = "SELECT * FROM plans"
    if not include_archived:
        sql += " WHERE plan_status<>'archived'"
    sql += " ORDER BY updated_at DESC"
    with connect(root) as conn:
        candidates = rows(conn.execute(sql))
    matches: list[dict[str, Any]] = []
    for record in candidates:
        indexed_text = " ".join(
            str(record[field])
            for field in (
                "plan_id", "title", "current_directory_name", "plan_status",
                "execution_status", "acceptance_status",
            )
        ).casefold()
        try:
            package = normalize_package(
                root, root.resolve() / record["current_relative_path"]
            )
            readme = package / "README.md"
            body = readme.read_text(
                encoding="utf-8", errors="replace"
            ).casefold()
        except (WopError, OSError):
            body = ""
        if needle in indexed_text or needle in body:
            matches.append(record)
    return matches


def relations(root: Path, plan_id: str) -> list[dict[str, Any]]:
    get_plan(root, plan_id=plan_id)
    with connect(root) as conn:
        return rows(
            conn.execute(
                "SELECT * FROM plan_relations WHERE source_plan_id=? OR target_plan_id=? "
                "ORDER BY created_at",
                (plan_id, plan_id),
            )
        )


def _dependency_graph(conn: sqlite3.Connection) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for row in conn.execute(
        "SELECT source_plan_id,target_plan_id FROM plan_relations "
        "WHERE relation_type='depends_on'"
    ):
        graph.setdefault(row["source_plan_id"], set()).add(row["target_plan_id"])
        graph.setdefault(row["target_plan_id"], set())
    return graph


def dependency_cycles(conn: sqlite3.Connection) -> list[list[str]]:
    graph = _dependency_graph(conn)
    visited: set[str] = set()
    active: list[str] = []
    active_set: set[str] = set()
    cycles: list[list[str]] = []

    def visit(node: str) -> None:
        if node in active_set:
            start = active.index(node)
            cycle = active[start:] + [node]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if node in visited:
            return
        active.append(node)
        active_set.add(node)
        for target in sorted(graph.get(node, set())):
            visit(target)
        active.pop()
        active_set.remove(node)
        visited.add(node)

    for node in sorted(graph):
        visit(node)
    return cycles


def create_relation(
    root: Path, source_id: str, target_id: str, relation_type: str, rationale: str
) -> dict[str, Any]:
    validate_uuid(source_id)
    validate_uuid(target_id)
    if relation_type not in RELATION_TYPES:
        raise WopError("Invalid relation type: {0}".format(relation_type))
    if source_id == target_id:
        raise WopError("A plan cannot relate to itself.")
    if not rationale.strip():
        raise WopError("A relationship rationale is required.")
    get_plan(root, plan_id=source_id)
    get_plan(root, plan_id=target_id)
    with connect(root) as conn:
        if relation_type == "depends_on":
            graph = _dependency_graph(conn)
            frontier = [target_id]
            seen: set[str] = set()
            while frontier:
                node = frontier.pop()
                if node == source_id:
                    raise WopError(
                        "depends_on relation would introduce a dependency cycle."
                    )
                if node in seen:
                    continue
                seen.add(node)
                frontier.extend(graph.get(node, set()))
        conn.execute(
            "INSERT INTO plan_relations(source_plan_id,target_plan_id,relation_type,"
            "rationale,created_at) VALUES(?,?,?,?,?)",
            (source_id, target_id, relation_type, rationale.strip(), now()),
        )
        add_event(
            conn,
            source_id,
            "relation_created",
            {"target_plan_id": target_id, "relation_type": relation_type},
        )
    return {
        "source_plan_id": source_id,
        "target_plan_id": target_id,
        "relation_type": relation_type,
        "rationale": rationale.strip(),
    }


def history(root: Path, plan_id: str) -> list[dict[str, Any]]:
    get_plan(root, plan_id=plan_id)
    with connect(root) as conn:
        return rows(
            conn.execute(
                "SELECT * FROM plan_revisions WHERE plan_id=? "
                "ORDER BY timestamp,revision_id",
                (plan_id,),
            )
        )


def evidence(root: Path, plan_id: str) -> list[dict[str, Any]]:
    get_plan(root, plan_id=plan_id)
    with connect(root) as conn:
        return rows(
            conn.execute(
                "SELECT * FROM plan_evidence WHERE plan_id=? "
                "ORDER BY recorded_at,evidence_id",
                (plan_id,),
            )
        )


def rename_package(
    root: Path,
    plan_id: str,
    new_directory: str,
    summary: str = "Package renamed",
    source: str = "rename",
) -> dict[str, Any]:
    record = get_plan(root, plan_id=plan_id)
    old_path = normalize_package(root, root.resolve() / record["current_relative_path"])
    target = normalize_package(root, new_directory, must_exist=False)
    if old_path.parent != target.parent:
        raise WopError("Use archive or restore to move between active and archive.")
    if target.exists():
        raise WopError("Rename target already exists: {0}".format(target))
    meta = metadata_from_package(old_path)
    if meta["plan_id"] != plan_id or meta["created_at"] != record["created_at"]:
        raise WopError("Revision must preserve plan_id and created_at.")
    package_hash = content_hash(old_path)
    content_changed = package_hash != record["content_hash"]
    if content_changed:
        if meta["version"] != record["version"] + 1:
            raise WopError(
                "Content changed; README version must increment exactly once."
            )
        if meta["updated_at"] == record["updated_at"]:
            raise WopError("Content changed; README updated_at must change.")
        integrity, message = prompt_integrity_detail(old_path, root)
        if integrity != "valid":
            raise WopError(
                "Revised package is not valid ({0}): {1}".format(integrity, message)
            )
    elif meta["version"] != record["version"]:
        raise WopError("Administrative rename cannot change the content version.")
    operation_id = start_operation(root, plan_id, "rename", old_path, target)
    try:
        old_path.rename(target)
    except Exception as exc:
        finish_operation(
            root,
            operation_id,
            "rolled_back",
            {
                "error": str(exc),
                "filesystem_unchanged": old_path.exists() and not target.exists(),
            },
        )
        raise
    try:
        with connect(root) as conn:
            if content_changed:
                conn.execute(
                    "UPDATE plans SET title=?,current_directory_name=?,"
                    "current_relative_path=?,updated_at=?,version=?,language=?,complexity=?,"
                    "content_hash=?,prompt_integrity_status='valid',"
                    "artifact_integrity_status='valid' WHERE plan_id=?",
                    (
                        meta["title"],
                        target.name,
                        relative_path(root, target),
                        meta["updated_at"],
                        meta["version"],
                        meta["language"],
                        meta["complexity"],
                        content_hash(target),
                        plan_id,
                    ),
                )
                add_revision(
                    conn,
                    plan_id,
                    meta["version"],
                    summary,
                    source,
                    old_path.name,
                    target.name,
                )
            else:
                conn.execute(
                    "UPDATE plans SET current_directory_name=?,current_relative_path=? "
                    "WHERE plan_id=?",
                    (target.name, relative_path(root, target), plan_id),
                )
            add_event(
                conn,
                plan_id,
                "revised" if content_changed else "renamed",
                {
                    "previous": old_path.name,
                    "current": target.name,
                    "content_changed": content_changed,
                },
            )
    except Exception as exc:
        try:
            target.rename(old_path)
        except Exception as rollback_exc:
            finish_operation(
                root,
                operation_id,
                "failed",
                {
                    "error": str(exc),
                    "rollback_error": str(rollback_exc),
                    "source_path": str(old_path),
                    "target_path": str(target),
                    "database_transaction_rolled_back": True,
                },
            )
            raise WopError(
                "Database update failed and filesystem rollback also failed; package "
                "may remain at {0}. Inspect operation {1}.".format(target, operation_id)
            ) from rollback_exc
        finish_operation(
            root,
            operation_id,
            "rolled_back",
            {"error": str(exc), "package_restored_to": str(old_path)},
        )
        raise
    finish_operation(
        root,
        operation_id,
        "completed",
        {"path": str(target), "content_changed": content_changed},
    )
    return get_plan(root, plan_id=plan_id)


def _evidence_counts(conn: sqlite3.Connection, plan_id: str) -> Tuple[int, int]:
    row = conn.execute(
        "SELECT "
        "SUM(CASE WHEN evidence_type IN ('execution','execution_and_acceptance') "
        "THEN 1 ELSE 0 END),"
        "SUM(CASE WHEN evidence_type IN ('acceptance','execution_and_acceptance') "
        "THEN 1 ELSE 0 END) "
        "FROM plan_evidence WHERE plan_id=?",
        (plan_id,),
    ).fetchone()
    return int(row[0] or 0), int(row[1] or 0)


def set_status(
    root: Path,
    plan_id: str,
    plan_status: Optional[str],
    execution_status: Optional[str],
    acceptance_status: Optional[str],
    evidence_references: Sequence[str] = (),
    evidence_summary: str = "",
    actor: str = "unspecified",
    human_approved: bool = False,
) -> dict[str, Any]:
    if not any((plan_status, execution_status, acceptance_status)):
        raise WopError("Provide at least one status change.")
    if plan_status == "archived":
        raise WopError("Use the archive command to set archived state.")
    current = get_plan(root, plan_id=plan_id)
    if current["plan_status"] == "archived":
        raise WopError("Restore an archived plan before changing its status.")
    final_plan = plan_status or current["plan_status"]
    final_execution = execution_status or current["execution_status"]
    final_acceptance = acceptance_status or current["acceptance_status"]
    if plan_status and plan_status not in PLAN_STATUSES:
        raise WopError("Invalid plan_status: {0}".format(plan_status))
    if execution_status and execution_status not in EXECUTION_STATUSES:
        raise WopError("Invalid execution_status: {0}".format(execution_status))
    if acceptance_status and acceptance_status not in ACCEPTANCE_STATUSES:
        raise WopError("Invalid acceptance_status: {0}".format(acceptance_status))
    package = normalize_package(root, root.resolve() / current["current_relative_path"])
    if final_plan == "ready":
        integrity, message = prompt_integrity_detail(package, root)
        if integrity != "valid":
            raise WopError(
                "Cannot set ready; integrity is {0}: {1}".format(integrity, message)
            )
    references = [value.strip() for value in evidence_references if value.strip()]
    if references and (not evidence_summary.strip() or not actor.strip()):
        raise WopError("Evidence requires a summary and identifiable actor.")
    with connect(root) as conn:
        execution_count, acceptance_count = _evidence_counts(conn, plan_id)
    adds_execution = bool(
        references
        and (
            final_execution == "executed"
            or final_plan in ("completed", "accepted")
        )
    )
    adds_acceptance = bool(
        references
        and (final_acceptance == "accepted" or final_plan == "accepted")
    )
    if final_plan in ("completed", "accepted") and final_execution != "executed":
        raise WopError(
            "completed or accepted plan_status requires execution_status=executed."
        )
    if final_execution == "executed" and not (execution_count or adds_execution):
        raise WopError(
            "execution_status=executed requires recorded execution evidence."
        )
    if final_plan == "accepted" and final_acceptance != "accepted":
        raise WopError(
            "plan_status=accepted requires acceptance_status=accepted."
        )
    if final_acceptance == "accepted" and not (acceptance_count or adds_acceptance):
        raise WopError(
            "acceptance_status=accepted requires recorded acceptance evidence."
        )
    operation_id = start_operation(root, plan_id, "set_status", package, package)
    original = update_frontmatter_projection(
        package,
        {
            "plan_status": final_plan,
            "execution_status": final_execution,
            "acceptance_status": final_acceptance,
        },
    )
    evidence_ids: list[str] = []
    try:
        with connect(root) as conn:
            for reference in references:
                evidence_id = str(uuid.uuid4())
                evidence_type = (
                    "execution_and_acceptance"
                    if adds_execution and adds_acceptance
                    else "execution" if adds_execution else "acceptance"
                )
                conn.execute(
                    "INSERT INTO plan_evidence(evidence_id,plan_id,evidence_type,"
                    "reference,summary,actor,human_approved,recorded_at) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (
                        evidence_id,
                        plan_id,
                        evidence_type,
                        reference,
                        evidence_summary.strip(),
                        actor.strip(),
                        1 if human_approved else 0,
                        now(),
                    ),
                )
                evidence_ids.append(evidence_id)
            conn.execute(
                "UPDATE plans SET plan_status=?,execution_status=?,acceptance_status=?,"
                "content_hash=?,artifact_integrity_status=? WHERE plan_id=?",
                (
                    final_plan,
                    final_execution,
                    final_acceptance,
                    content_hash(package),
                    prompt_integrity(package, root),
                    plan_id,
                ),
            )
            add_event(
                conn,
                plan_id,
                "status_changed",
                {
                    "from": {
                        "plan_status": current["plan_status"],
                        "execution_status": current["execution_status"],
                        "acceptance_status": current["acceptance_status"],
                    },
                    "to": {
                        "plan_status": final_plan,
                        "execution_status": final_execution,
                        "acceptance_status": final_acceptance,
                    },
                    "evidence_ids": evidence_ids,
                    "human_approved": human_approved,
                },
            )
    except Exception as exc:
        restore_readme(package, original)
        finish_operation(
            root,
            operation_id,
            "rolled_back",
            {"error": str(exc), "readme_projection_restored": True},
        )
        raise
    finish_operation(
        root,
        operation_id,
        "completed",
        {"evidence_ids": evidence_ids, "readme_projection_updated": True},
    )
    return get_plan(root, plan_id=plan_id)


def move_package(root: Path, plan_id: str, archive: bool) -> dict[str, Any]:
    record = get_plan(root, plan_id=plan_id)
    old_path = normalize_package(root, root.resolve() / record["current_relative_path"])
    expected_parent = "plans" if archive else "archive"
    if old_path.parent.name != expected_parent:
        raise WopError("Plan is not active." if archive else "Plan is not archived.")
    target_parent = workspace(root) / ("archive" if archive else "plans")
    target = normalize_package(root, target_parent / old_path.name, must_exist=False)
    if target.exists():
        raise WopError("Destination collision: {0}".format(target))
    restored_status = (
        record["plan_status"]
        if archive
        else record.get("pre_archive_plan_status") or "draft"
    )
    projected_status = "archived" if archive else restored_status
    operation_type = "archive" if archive else "restore"
    operation_id = start_operation(root, plan_id, operation_type, old_path, target)
    try:
        shutil.move(str(old_path), str(target))
    except Exception as exc:
        finish_operation(
            root,
            operation_id,
            "rolled_back",
            {
                "error": str(exc),
                "filesystem_unchanged": old_path.exists() and not target.exists(),
            },
        )
        raise
    original: Optional[bytes] = None
    try:
        original = update_frontmatter_projection(
            target, {"plan_status": projected_status}
        )
        timestamp = now()
        with connect(root) as conn:
            conn.execute(
                "UPDATE plans SET current_relative_path=?,plan_status=?,archived_at=?,"
                "pre_archive_plan_status=?,content_hash=?,artifact_integrity_status=? "
                "WHERE plan_id=?",
                (
                    relative_path(root, target),
                    projected_status,
                    timestamp if archive else None,
                    record["plan_status"] if archive else None,
                    content_hash(target),
                    prompt_integrity(target, root),
                    plan_id,
                ),
            )
            add_event(
                conn,
                plan_id,
                "archived" if archive else "restored",
                {
                    "path": relative_path(root, target),
                    "previous_plan_status": record["plan_status"],
                    "restored_plan_status": restored_status if not archive else None,
                },
            )
    except Exception as exc:
        if original is not None and target.exists():
            restore_readme(target, original)
        rollback_error: Optional[Exception] = None
        if target.exists() and not old_path.exists():
            try:
                shutil.move(str(target), str(old_path))
            except Exception as rollback_exc:
                rollback_error = rollback_exc
        if rollback_error is not None:
            finish_operation(
                root,
                operation_id,
                "failed",
                {
                    "error": str(exc),
                    "rollback_error": str(rollback_error),
                    "source_path": str(old_path),
                    "target_path": str(target),
                    "database_transaction_rolled_back": True,
                },
            )
            raise WopError(
                "{0} failed and filesystem rollback also failed; inspect operation "
                "{1}, source {2}, and target {3}.".format(
                    operation_type, operation_id, old_path, target
                )
            ) from rollback_error
        finish_operation(
            root,
            operation_id,
            "rolled_back",
            {
                "error": str(exc),
                "package_restored_to": str(old_path),
                "database_unchanged": True,
            },
        )
        raise
    finish_operation(
        root,
        operation_id,
        "completed",
        {"path": str(target), "plan_status": projected_status},
    )
    return get_plan(root, plan_id=plan_id)


def delete_plan(root: Path, plan_id: str, confirmed: bool, reason: str) -> dict[str, Any]:
    if not confirmed:
        raise WopError("Permanent deletion requires --confirm.")
    if not reason.strip():
        raise WopError("Permanent deletion requires a reason.")
    record = get_plan(root, plan_id=plan_id)
    package = normalize_package(root, root.resolve() / record["current_relative_path"])
    with connect(root) as conn:
        dependent = rows(
            conn.execute(
                "SELECT * FROM plan_relations WHERE target_plan_id=? "
                "AND relation_type='depends_on'",
                (plan_id,),
            )
        )
        if dependent:
            raise WopError(
                "Dependent plans exist; remove or revise relationships before deletion."
            )
        related = rows(
            conn.execute(
                "SELECT * FROM plan_relations WHERE source_plan_id=? OR target_plan_id=?",
                (plan_id, plan_id),
            )
        )
    staged = package.with_name(package.name + ".deleting-" + uuid.uuid4().hex)
    if staged.exists():
        raise WopError("Recovery path already exists: {0}".format(staged))
    operation_id = start_operation(root, plan_id, "delete", package, staged)
    try:
        package.rename(staged)
    except Exception as exc:
        finish_operation(
            root,
            operation_id,
            "rolled_back",
            {
                "error": str(exc),
                "filesystem_unchanged": package.exists() and not staged.exists(),
            },
        )
        raise
    try:
        with connect(root) as conn:
            conn.execute(
                "DELETE FROM plan_relations WHERE source_plan_id=? OR target_plan_id=?",
                (plan_id, plan_id),
            )
            conn.execute("DELETE FROM plans WHERE plan_id=?", (plan_id,))
            conn.execute(
                "INSERT INTO plan_tombstones(plan_id,deleted_at,"
                "previous_directory_name,deletion_reason) VALUES(?,?,?,?)",
                (plan_id, now(), package.name, reason.strip()),
            )
            add_event(
                conn,
                plan_id,
                "deleted",
                {
                    "previous_directory_name": package.name,
                    "relationships_removed": related,
                    "staged_path": str(staged),
                },
            )
    except Exception as exc:
        try:
            staged.rename(package)
        except Exception as rollback_exc:
            finish_operation(
                root,
                operation_id,
                "failed",
                {
                    "error": str(exc),
                    "rollback_error": str(rollback_exc),
                    "database_transaction_rolled_back": True,
                    "staged_package": str(staged),
                },
            )
            raise WopError(
                "Delete database step failed and staged-package rollback also failed; "
                "inspect operation {0} and {1}.".format(operation_id, staged)
            ) from rollback_exc
        finish_operation(
            root,
            operation_id,
            "rolled_back",
            {"error": str(exc), "package_restored_to": str(package)},
        )
        raise
    try:
        shutil.rmtree(staged)
    except OSError as exc:
        finish_operation(
            root,
            operation_id,
            "failed",
            {
                "error": str(exc),
                "database_deleted": True,
                "tombstone_retained": True,
                "staged_package_requires_cleanup": str(staged),
            },
        )
        raise WopError(
            "Database deletion committed and tombstone retained, but staged package "
            "cleanup failed at {0}: {1}".format(staged, exc)
        ) from exc
    finish_operation(
        root,
        operation_id,
        "completed",
        {"tombstone_retained": True, "package_removed": True},
    )
    return {
        "plan_id": plan_id,
        "deleted": True,
        "previous_directory_name": package.name,
        "tombstone_retained": True,
    }


def _issue(
    issues: list[dict[str, str]],
    status: str,
    code: str,
    plan_id: str,
    message: str,
) -> None:
    issues.append(
        {"status": status, "code": code, "plan_id": plan_id, "message": message}
    )


def check(root: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    with connect(root) as conn:
        db_integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_key_issues = rows(conn.execute("PRAGMA foreign_key_check"))
        records = rows(conn.execute("SELECT * FROM plans"))
        tombstones = {
            row["plan_id"] for row in conn.execute("SELECT plan_id FROM plan_tombstones")
        }
        cycles = dependency_cycles(conn)
        pending_operations = rows(
            conn.execute(
                "SELECT * FROM plan_operations WHERE status IN ('pending','failed')"
            )
        )
    for cycle in cycles:
        _issue(
            issues,
            "conflict",
            "dependency_cycle",
            cycle[0],
            "depends_on cycle: {0}".format(" -> ".join(cycle)),
        )
    for operation in pending_operations:
        _issue(
            issues,
            "conflict",
            "unfinished_operation",
            operation["plan_id"],
            "Operation {0} is {1}: {2}".format(
                operation["operation_id"], operation["status"], operation["details"]
            ),
        )
    indexed_paths: set[str] = set()
    for record in records:
        plan_id = record["plan_id"]
        raw_path = root.resolve() / record["current_relative_path"]
        try:
            path = normalize_package(root, raw_path)
        except WopError as exc:
            code = "missing_package" if not raw_path.exists() else "unsafe_package_path"
            status = "missing" if code == "missing_package" else "conflict"
            _issue(issues, status, code, plan_id, str(exc))
            continue
        indexed_paths.add(str(path))
        if path.name != record["current_directory_name"]:
            _issue(
                issues,
                "conflict",
                "directory_mismatch",
                plan_id,
                "Filesystem directory differs from the indexed name.",
            )
        expected_relative = relative_path(root, path)
        if expected_relative != record["current_relative_path"]:
            _issue(
                issues,
                "conflict",
                "path_mismatch",
                plan_id,
                "Resolved relative path differs from the indexed path.",
            )
        try:
            meta = metadata_from_package(path)
        except (WopError, UnicodeError, OSError) as exc:
            _issue(issues, "invalid", "malformed_package", plan_id, str(exc))
            continue
        for key in (
            "plan_id", "title", "created_at", "updated_at", "version",
            "language", "complexity", "plan_status", "execution_status",
            "acceptance_status",
        ):
            if str(meta[key]) != str(record[key]):
                _issue(
                    issues,
                    "conflict",
                    "metadata_mismatch",
                    plan_id,
                    "README {0} differs from SQLite.".format(key),
                )
        if plan_id in tombstones:
            _issue(
                issues,
                "conflict",
                "tombstone_reuse",
                plan_id,
                "An indexed plan reuses a tombstoned ID.",
            )
        if path.parent.name == "archive" and record["plan_status"] != "archived":
            _issue(
                issues,
                "conflict",
                "archive_status_mismatch",
                plan_id,
                "Archived package is not indexed as archived.",
            )
        if path.parent.name == "plans" and record["plan_status"] == "archived":
            _issue(
                issues,
                "conflict",
                "active_status_mismatch",
                plan_id,
                "Active package is indexed as archived.",
            )
        actual_hash = content_hash(path)
        if actual_hash != record["content_hash"]:
            _issue(
                issues,
                "conflict",
                "content_hash_mismatch",
                plan_id,
                "Indexed package hash differs from filesystem artifacts.",
            )
        integrity, detail = prompt_integrity_detail(path, root)
        if integrity != "valid":
            _issue(
                issues,
                integrity,
                "artifact_integrity",
                plan_id,
                detail,
            )
        if record["artifact_integrity_status"] != integrity:
            _issue(
                issues,
                "conflict",
                "integrity_projection_mismatch",
                plan_id,
                "Stored integrity status {0} differs from observed {1}.".format(
                    record["artifact_integrity_status"], integrity
                ),
            )
        expected_prompt_integrity = (
            integrity if integrity in ("valid", "invalid", "unchecked") else "invalid"
        )
        if record["prompt_integrity_status"] != expected_prompt_integrity:
            _issue(
                issues,
                "conflict",
                "prompt_integrity_projection_mismatch",
                plan_id,
                "Stored prompt integrity {0} differs from observed {1}.".format(
                    record["prompt_integrity_status"], expected_prompt_integrity
                ),
            )
    for base in (workspace(root) / "plans", workspace(root) / "archive"):
        for package in sorted(path for path in base.iterdir() if path.is_dir()):
            if ".deleting-" in package.name:
                _issue(
                    issues,
                    "conflict",
                    "staged_delete_package",
                    "",
                    "Staged deletion package requires recovery: {0}".format(package),
                )
            elif str(package.resolve()) not in indexed_paths:
                _issue(
                    issues,
                    "missing",
                    "unindexed_package",
                    "",
                    "Package exists but is not indexed: {0}".format(package),
                )
    status_counts = {status: 0 for status in INTEGRITY_STATUSES}
    if not issues:
        status_counts["valid"] = len(records)
    for item in issues:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1
    return {
        "ok": db_integrity == "ok" and not foreign_key_issues and not issues,
        "database_integrity": db_integrity,
        "foreign_key_issues": foreign_key_issues,
        "integrity_status_counts": status_counts,
        "issues": issues,
        "recovery": (
            "Resolve conflict, missing, invalid, and unchecked results explicitly. "
            "Use rebuild only for reviewed packages; it preserves existing operational "
            "states and never invents execution or acceptance evidence."
        ),
    }


def rebuild(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "registered": [], "updated": [], "conflicts": [], "errors": []
    }
    initialize(root)
    with connect(root) as conn:
        tombstones = {
            row["plan_id"] for row in conn.execute("SELECT plan_id FROM plan_tombstones")
        }
    candidates: list[Tuple[Path, Path, dict[str, Any]]] = []
    for base in (workspace(root) / "plans", workspace(root) / "archive"):
        for package in sorted(path for path in base.iterdir() if path.is_dir()):
            if ".deleting-" in package.name:
                result["errors"].append(
                    {
                        "package": str(package),
                        "error": "Interrupted deletion package requires manual resolution.",
                    }
                )
                continue
            try:
                package = normalize_package(root, package)
                meta = metadata_from_package(package)
                if meta["plan_id"] in tombstones:
                    raise WopError(
                        "Tombstoned ID is reused: {0}".format(meta["plan_id"])
                    )
                candidates.append((base, package, meta))
            except (WopError, OSError, sqlite3.Error) as exc:
                result["errors"].append({"package": str(package), "error": str(exc)})
    by_id: dict[str, list[Tuple[Path, Path, dict[str, Any]]]] = {}
    for candidate in candidates:
        by_id.setdefault(candidate[2]["plan_id"], []).append(candidate)
    for plan_id, matches in by_id.items():
        if len(matches) > 1:
            result["errors"].append(
                {
                    "package": ", ".join(str(item[1]) for item in matches),
                    "error": "Ambiguous duplicate plan_id {0}.".format(plan_id),
                }
            )
            continue
        base, package, meta = matches[0]
        try:
            integrity, detail = prompt_integrity_detail(package, root)
            with connect(root) as conn:
                existing_row = conn.execute(
                    "SELECT * FROM plans WHERE plan_id=?", (plan_id,)
                ).fetchone()
                existing = dict(existing_row) if existing_row else None
                if existing:
                    for field in (
                        "plan_status", "execution_status", "acceptance_status"
                    ):
                        if str(meta[field]) != str(existing[field]):
                            result["conflicts"].append(
                                {
                                    "plan_id": plan_id,
                                    "field": field,
                                    "readme": meta[field],
                                    "sqlite_preserved": existing[field],
                                    "message": (
                                        "README operational projection is stale; "
                                        "SQLite state was preserved."
                                    ),
                                }
                            )
                    if meta["created_at"] != existing["created_at"]:
                        result["conflicts"].append(
                            {
                                "plan_id": plan_id,
                                "field": "created_at",
                                "readme": meta["created_at"],
                                "sqlite_preserved": existing["created_at"],
                                "message": "Stable creation timestamp conflict.",
                            }
                        )
                    if meta["version"] < existing["version"]:
                        raise WopError(
                            "README version is older than the indexed version."
                        )
                    updated_at = (
                        meta["updated_at"]
                        if meta["version"] > existing["version"]
                        else existing["updated_at"]
                    )
                    conn.execute(
                        "UPDATE plans SET title=?,current_directory_name=?,"
                        "current_relative_path=?,updated_at=?,version=?,language=?,"
                        "complexity=?,content_hash=?,prompt_integrity_status=?,"
                        "artifact_integrity_status=? WHERE plan_id=?",
                        (
                            meta["title"],
                            package.name,
                            relative_path(root, package),
                            updated_at,
                            max(meta["version"], existing["version"]),
                            meta["language"],
                            meta["complexity"],
                            content_hash(package),
                            integrity
                            if integrity in ("valid", "invalid", "unchecked")
                            else "invalid",
                            integrity,
                            plan_id,
                        ),
                    )
                    result["updated"].append(plan_id)
                else:
                    initial_plan_status = (
                        "archived"
                        if base.name == "archive"
                        else "ready"
                        if meta["plan_status"] == "ready" and integrity == "valid"
                        else "draft"
                    )
                    conn.execute(
                        "INSERT INTO plans(plan_id,title,current_directory_name,"
                        "current_relative_path,created_at,updated_at,version,language,"
                        "complexity,plan_status,execution_status,acceptance_status,"
                        "archived_at,pre_archive_plan_status,content_hash,"
                        "prompt_integrity_status,artifact_integrity_status) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            plan_id,
                            meta["title"],
                            package.name,
                            relative_path(root, package),
                            meta["created_at"],
                            meta["updated_at"],
                            meta["version"],
                            meta["language"],
                            meta["complexity"],
                            initial_plan_status,
                            "not_started",
                            "not_evaluated",
                            now() if base.name == "archive" else None,
                            (
                                meta["plan_status"]
                                if base.name == "archive"
                                and meta["plan_status"] != "archived"
                                else None
                            ),
                            content_hash(package),
                            integrity
                            if integrity in ("valid", "invalid", "unchecked")
                            else "invalid",
                            integrity,
                        ),
                    )
                    add_revision(
                        conn,
                        plan_id,
                        meta["version"],
                        "Index rebuilt from package",
                        "rebuild",
                        None,
                        package.name,
                    )
                    add_event(
                        conn,
                        plan_id,
                        "rebuilt",
                        {
                            "path": relative_path(root, package),
                            "execution_status": "not_started",
                            "acceptance_status": "not_evaluated",
                            "integrity": integrity,
                        },
                    )
                    result["registered"].append(plan_id)
                    if meta["execution_status"] != "not_started":
                        result["conflicts"].append(
                            {
                                "plan_id": plan_id,
                                "field": "execution_status",
                                "readme": meta["execution_status"],
                                "sqlite_preserved": "not_started",
                                "message": "No execution evidence existed in the rebuilt index.",
                            }
                        )
                    if meta["acceptance_status"] != "not_evaluated":
                        result["conflicts"].append(
                            {
                                "plan_id": plan_id,
                                "field": "acceptance_status",
                                "readme": meta["acceptance_status"],
                                "sqlite_preserved": "not_evaluated",
                                "message": "No acceptance evidence existed in the rebuilt index.",
                            }
                        )
            if integrity in ("unchecked", "missing", "invalid", "conflict"):
                result["errors"].append(
                    {
                        "package": str(package),
                        "error": "Integrity is {0}: {1}".format(integrity, detail),
                    }
                )
        except (WopError, OSError, sqlite3.Error) as exc:
            result["errors"].append({"package": str(package), "error": str(exc)})
    result["ok"] = not result["errors"] and not result["conflicts"]
    return result


def parser() -> argparse.ArgumentParser:
    main = argparse.ArgumentParser(description=__doc__)
    main.add_argument("--root", required=True, type=Path, help="Project root")
    main.add_argument("--json", action="store_true", help="Emit JSON")
    sub = main.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("--plan-status", choices=PLAN_STATUSES)
    list_cmd.add_argument("--execution-status", choices=EXECUTION_STATUSES)
    list_cmd.add_argument("--include-archived", action="store_true")

    search_cmd = sub.add_parser("search")
    search_cmd.add_argument("--query", required=True)
    search_cmd.add_argument("--active-only", action="store_true")

    get_cmd = sub.add_parser("get")
    group = get_cmd.add_mutually_exclusive_group(required=True)
    group.add_argument("--id")
    group.add_argument("--name")

    relations_cmd = sub.add_parser("relations")
    relations_cmd.add_argument("--id", required=True)

    relate_cmd = sub.add_parser("relate")
    relate_cmd.add_argument("--source-id", required=True)
    relate_cmd.add_argument("--target-id", required=True)
    relate_cmd.add_argument("--type", required=True, choices=RELATION_TYPES)
    relate_cmd.add_argument("--rationale", required=True)

    history_cmd = sub.add_parser("history")
    history_cmd.add_argument("--id", required=True)
    evidence_cmd = sub.add_parser("evidence")
    evidence_cmd.add_argument("--id", required=True)

    sub.add_parser("check")
    sub.add_parser("rebuild")

    register_cmd = sub.add_parser("register")
    register_cmd.add_argument("--directory", required=True)

    rename_cmd = sub.add_parser("rename")
    rename_cmd.add_argument("--id", required=True)
    rename_cmd.add_argument("--new-directory", required=True)
    rename_cmd.add_argument("--summary", default="Package renamed")
    rename_cmd.add_argument("--source", default="rename")

    status_cmd = sub.add_parser("set-status")
    status_cmd.add_argument("--id", required=True)
    status_cmd.add_argument("--plan-status", choices=PLAN_STATUSES)
    status_cmd.add_argument("--execution-status", choices=EXECUTION_STATUSES)
    status_cmd.add_argument("--acceptance-status", choices=ACCEPTANCE_STATUSES)
    status_cmd.add_argument("--evidence-reference", action="append", default=[])
    status_cmd.add_argument("--evidence-summary", default="")
    status_cmd.add_argument("--actor", default="unspecified")
    status_cmd.add_argument("--human-approved", action="store_true")

    archive_cmd = sub.add_parser("archive")
    archive_cmd.add_argument("--id", required=True)
    restore_cmd = sub.add_parser("restore")
    restore_cmd.add_argument("--id", required=True)

    delete_cmd = sub.add_parser("delete")
    delete_cmd.add_argument("--id", required=True)
    delete_cmd.add_argument("--confirm", action="store_true")
    delete_cmd.add_argument(
        "--reason", default="Explicitly confirmed permanent deletion"
    )
    return main


def render(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, indent=2, sort_keys=True, default=str))
        return
    if isinstance(value, list):
        if not value:
            print("No records.")
        for item in value:
            print(json.dumps(item, sort_keys=True, default=str))
    elif isinstance(value, dict):
        for key, item in value.items():
            print("{0}: {1}".format(key, item))
    else:
        print(value)


def run(argv: Optional[Sequence[str]] = None) -> int:
    args = parser().parse_args(argv)
    try:
        root = args.root.resolve()
        if args.command == "list":
            value = list_plans(
                root, args.plan_status, args.execution_status, args.include_archived
            )
        elif args.command == "search":
            value = search(root, args.query, not args.active_only)
        elif args.command == "get":
            value = get_plan(root, plan_id=args.id, name=args.name)
        elif args.command == "relations":
            value = relations(root, args.id)
        elif args.command == "relate":
            value = create_relation(
                root, args.source_id, args.target_id, args.type, args.rationale
            )
        elif args.command == "history":
            value = history(root, args.id)
        elif args.command == "evidence":
            value = evidence(root, args.id)
        elif args.command == "check":
            value = check(root)
        elif args.command == "rebuild":
            value = rebuild(root)
        elif args.command == "register":
            value = register(root, args.directory)
        elif args.command == "rename":
            value = rename_package(
                root, args.id, args.new_directory, args.summary, args.source
            )
        elif args.command == "set-status":
            value = set_status(
                root,
                args.id,
                args.plan_status,
                args.execution_status,
                args.acceptance_status,
                args.evidence_reference,
                args.evidence_summary,
                args.actor,
                args.human_approved,
            )
        elif args.command == "archive":
            value = move_package(root, args.id, True)
        elif args.command == "restore":
            value = move_package(root, args.id, False)
        elif args.command == "delete":
            value = delete_plan(root, args.id, args.confirm, args.reason)
        else:
            raise WopError("Unsupported command: {0}".format(args.command))
        render(value, args.json)
        if isinstance(value, dict) and value.get("ok") is False:
            return 2
        return 0
    except (WopError, OSError, sqlite3.Error, UnicodeError) as exc:
        error = {"error": str(exc), "type": exc.__class__.__name__}
        if args.json:
            print(json.dumps(error, indent=2), file=sys.stderr)
        else:
            print("error: {0}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
