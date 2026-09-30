from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import threading
import time

from .contracts import AppProductError, ControlConflict


SCHEMA_VERSION = 1
VALID_CONTROL_STATES = {"ACTIVE", "PAUSED", "CANCELLED"}


class OperatorStore:
    """Durable product-side metadata and control intent.

    Raw source bytes, engine artifacts and canonical stage state remain in the
    canonical BIE stores. This sidecar stores only display metadata and operator
    actions so UI concerns do not become a second engine.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init()

    def _conn(self):
        c = sqlite3.connect(str(self.path), timeout=30, isolation_level=None)
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA journal_mode=WAL")
        return c

    def _init(self):
        with self._lock, self._conn() as c:
            c.executescript(
                """
                BEGIN IMMEDIATE;
                CREATE TABLE IF NOT EXISTS schema_meta(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS source_index(
                    job_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    source_hash TEXT NOT NULL,
                    byte_length INTEGER NOT NULL,
                    media_type TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS controls(
                    job_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS control_events(
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    event_at REAL NOT NULL
                );
                COMMIT;
                """
            )
            row = c.execute("SELECT value FROM schema_meta WHERE key='schema_version'").fetchone()
            if row is None:
                c.execute(
                    "INSERT INTO schema_meta(key,value) VALUES('schema_version',?)",
                    (str(SCHEMA_VERSION),),
                )
            elif int(row[0]) != SCHEMA_VERSION:
                raise AppProductError("unsupported_operator_store_schema")

    def remember_source(
        self, job_id: str, display_name: str, source_hash: str, byte_length: int, media_type: str
    ) -> None:
        canonical = (display_name, source_hash, byte_length, media_type)
        with self._lock, self._conn() as c:
            c.execute("BEGIN IMMEDIATE")
            try:
                row = c.execute(
                    "SELECT display_name,source_hash,byte_length,media_type FROM source_index WHERE job_id=?",
                    (job_id,),
                ).fetchone()
                if row is None:
                    c.execute(
                        "INSERT INTO source_index(job_id,display_name,source_hash,byte_length,media_type,created_at) "
                        "VALUES(?,?,?,?,?,?)",
                        (job_id, *canonical, time.time()),
                    )
                elif tuple(row) != canonical:
                    raise AppProductError("source_index_immutable_conflict")
                c.execute(
                    "INSERT OR IGNORE INTO controls(job_id,state,reason,updated_at) VALUES(?,?,?,?)",
                    (job_id, "ACTIVE", "created", time.time()),
                )
                c.execute("COMMIT")
            except Exception:
                c.execute("ROLLBACK")
                raise

    def source(self, job_id: str) -> dict[str, object] | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT display_name,source_hash,byte_length,media_type,created_at FROM source_index WHERE job_id=?",
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "display_name": row[0],
            "source_hash": row[1],
            "byte_length": row[2],
            "media_type": row[3],
            "created_at": row[4],
        }

    def control_state(self, job_id: str) -> str:
        with self._conn() as c:
            row = c.execute("SELECT state FROM controls WHERE job_id=?", (job_id,)).fetchone()
        return "ACTIVE" if row is None else row[0]

    def transition(self, job_id: str, target: str, *, action: str, reason: str) -> str:
        if target not in VALID_CONTROL_STATES:
            raise AppProductError("invalid_control_target")
        if not reason.strip() or not action.strip():
            raise AppProductError("control_reason_and_action_required")
        allowed = {
            ("ACTIVE", "PAUSED"),
            ("ACTIVE", "CANCELLED"),
            ("PAUSED", "ACTIVE"),
            ("PAUSED", "CANCELLED"),
        }
        with self._lock, self._conn() as c:
            c.execute("BEGIN IMMEDIATE")
            try:
                row = c.execute("SELECT state FROM controls WHERE job_id=?", (job_id,)).fetchone()
                current = "ACTIVE" if row is None else row[0]
                if current == target:
                    c.execute("COMMIT")
                    return current
                if (current, target) not in allowed:
                    raise ControlConflict(f"control_transition_forbidden:{current}->{target}")
                if row is None:
                    c.execute(
                        "INSERT INTO controls(job_id,state,reason,updated_at) VALUES(?,?,?,?)",
                        (job_id, target, reason, time.time()),
                    )
                else:
                    c.execute(
                        "UPDATE controls SET state=?,reason=?,updated_at=? WHERE job_id=?",
                        (target, reason, time.time(), job_id),
                    )
                c.execute(
                    "INSERT INTO control_events(job_id,action,from_state,to_state,reason,event_at) "
                    "VALUES(?,?,?,?,?,?)",
                    (job_id, action, current, target, reason, time.time()),
                )
                c.execute("COMMIT")
                return target
            except Exception:
                c.execute("ROLLBACK")
                raise

    def record_retry(self, job_id: str, reason: str) -> None:
        if self.control_state(job_id) == "CANCELLED":
            raise ControlConflict("cancelled_run_cannot_retry")
        with self._lock, self._conn() as c:
            c.execute("BEGIN IMMEDIATE")
            try:
                c.execute(
                    "INSERT OR IGNORE INTO controls(job_id,state,reason,updated_at) VALUES(?,?,?,?)",
                    (job_id, "ACTIVE", "retry", time.time()),
                )
                current = c.execute("SELECT state FROM controls WHERE job_id=?", (job_id,)).fetchone()[0]
                if current == "PAUSED":
                    raise ControlConflict("paused_run_must_resume_before_retry")
                c.execute(
                    "INSERT INTO control_events(job_id,action,from_state,to_state,reason,event_at) "
                    "VALUES(?,?,?,?,?,?)",
                    (job_id, "RETRY", current, current, reason, time.time()),
                )
                c.execute("COMMIT")
            except Exception:
                c.execute("ROLLBACK")
                raise

    def events(self, job_id: str) -> tuple[dict[str, object], ...]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT sequence,action,from_state,to_state,reason,event_at "
                "FROM control_events WHERE job_id=? ORDER BY sequence",
                (job_id,),
            ).fetchall()
        return tuple(
            {
                "sequence": row[0],
                "action": row[1],
                "from_state": row[2],
                "to_state": row[3],
                "reason": row[4],
                "event_at": row[5],
            }
            for row in rows
        )
