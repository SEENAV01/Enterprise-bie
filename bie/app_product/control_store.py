from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import threading

from .contracts import require_identifier


VALID_CONTROL_STATES = {
    "ACTIVE",
    "PAUSED",
    "CANCEL_REQUESTED",
    "CANCELLED",
}
ALLOWED_TRANSITIONS = {
    "ACTIVE": {"PAUSED", "CANCEL_REQUESTED", "CANCELLED"},
    "PAUSED": {"ACTIVE", "CANCEL_REQUESTED", "CANCELLED"},
    "CANCEL_REQUESTED": {"CANCELLED"},
    "CANCELLED": set(),
}


class RunControlError(ValueError):
    pass


@dataclass(frozen=True)
class RunControl:
    run_id: str
    state: str
    revision: int
    updated_at: str


class RunControlStore:
    """Durable operator-control overlay bound to canonical run IDs.

    It stores only control intent. Canonical stage/artifact state remains in the
    existing BIE persistence/queue/CAS stores.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(str(self.path), timeout=30, isolation_level=None)
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _init_db(self) -> None:
        with self._lock, self._conn() as conn:
            conn.executescript(
                """
                BEGIN IMMEDIATE;
                CREATE TABLE IF NOT EXISTS run_controls(
                    run_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS run_control_events(
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    observed_at TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES run_controls(run_id)
                );
                COMMIT;
                """
            )

    def ensure_active(self, run_id: str) -> RunControl:
        run_id = require_identifier(run_id, "run_id")
        now = self._now()
        with self._lock, self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO run_controls(run_id,state,revision,updated_at) VALUES(?,?,?,?)",
                (run_id, "ACTIVE", 1, now),
            )
        return self.get(run_id)

    def get(self, run_id: str) -> RunControl:
        run_id = require_identifier(run_id, "run_id")
        with self._conn() as conn:
            row = conn.execute(
                "SELECT state,revision,updated_at FROM run_controls WHERE run_id=?",
                (run_id,),
            ).fetchone()
        if row is None:
            return self.ensure_active(run_id)
        if row[0] not in VALID_CONTROL_STATES or row[1] < 1:
            raise RunControlError("control_store_corrupt")
        return RunControl(run_id, row[0], int(row[1]), row[2])

    def transition(self, run_id: str, to_state: str, reason: str) -> RunControl:
        run_id = require_identifier(run_id, "run_id")
        reason = require_identifier(reason, "reason", max_length=512)
        if to_state not in VALID_CONTROL_STATES:
            raise RunControlError("invalid_control_state")
        self.ensure_active(run_id)
        with self._lock, self._conn() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    "SELECT state,revision FROM run_controls WHERE run_id=?",
                    (run_id,),
                ).fetchone()
                if row is None:
                    raise RunControlError("control_not_found")
                from_state, revision = row[0], int(row[1])
                if to_state == from_state:
                    conn.execute("COMMIT")
                    return self.get(run_id)
                if to_state not in ALLOWED_TRANSITIONS[from_state]:
                    raise RunControlError("invalid_control_transition")
                revision += 1
                now = self._now()
                conn.execute(
                    "UPDATE run_controls SET state=?,revision=?,updated_at=? WHERE run_id=?",
                    (to_state, revision, now, run_id),
                )
                conn.execute(
                    """INSERT INTO run_control_events(
                        run_id,from_state,to_state,revision,observed_at,reason
                    ) VALUES(?,?,?,?,?,?)""",
                    (run_id, from_state, to_state, revision, now, reason),
                )
                conn.execute("COMMIT")
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
        return self.get(run_id)

    def events(self, run_id: str) -> tuple[dict[str, object], ...]:
        run_id = require_identifier(run_id, "run_id")
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT sequence,from_state,to_state,revision,observed_at,reason
                   FROM run_control_events WHERE run_id=? ORDER BY sequence""",
                (run_id,),
            ).fetchall()
        return tuple(
            {
                "sequence": int(row[0]),
                "from_state": row[1],
                "to_state": row[2],
                "revision": int(row[3]),
                "observed_at": row[4],
                "reason": row[5],
            }
            for row in rows
        )
