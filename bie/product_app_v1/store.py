from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import hashlib
import json
import sqlite3
import threading
import time

from .models import (
    AttemptSnapshot,
    CREATE_KEY_RE,
    OperatorConflict,
    OperatorError,
    OperatorEvent,
    RunSnapshot,
    SAFE_STATES,
)

SCHEMA_VERSION = 1
RUN_POLICY = "bie-section18-operator-run-v1"


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def derive_run_id(create_key: str) -> str:
    if type(create_key) is not str or not CREATE_KEY_RE.fullmatch(create_key):
        raise OperatorError("invalid_create_key")
    digest = hashlib.sha256((RUN_POLICY + "\0" + create_key).encode("utf-8")).hexdigest()
    return "oprun-" + digest


class SQLiteOperatorStore:
    """Durable product/operator metadata.

    The store intentionally does not duplicate BIE engine artifacts or source
    bytes. Canonical jobs, queue state, CAS content and evidence stay in the
    existing BIE stores. This database records product identity, current
    attempt binding and operator events only.
    """

    def __init__(self, path: Path, *, clock=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock or time.time
        self._lock = threading.RLock()
        self._init_db()

    def _now(self) -> float:
        return float(self.clock())

    def _connect(self):
        c = sqlite3.connect(str(self.path), timeout=30, isolation_level=None)
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA journal_mode=WAL")
        return c

    def _init_db(self) -> None:
        with self._lock, self._connect() as c:
            c.executescript("""
            BEGIN IMMEDIATE;
            CREATE TABLE IF NOT EXISTS schema_meta(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS operator_runs(
                run_id TEXT PRIMARY KEY,
                create_key TEXT NOT NULL UNIQUE,
                state TEXT NOT NULL,
                current_attempt INTEGER NOT NULL,
                source_hash TEXT,
                source_name TEXT,
                canonical_job_id TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS operator_attempts(
                run_id TEXT NOT NULL,
                attempt INTEGER NOT NULL,
                canonical_job_id TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                source_hash TEXT NOT NULL,
                state TEXT NOT NULL,
                retry_of_job_id TEXT,
                created_at REAL NOT NULL,
                PRIMARY KEY(run_id,attempt),
                UNIQUE(canonical_job_id),
                FOREIGN KEY(run_id) REFERENCES operator_runs(run_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS operator_events(
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                created_at REAL NOT NULL,
                payload_json TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES operator_runs(run_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_operator_events_run
              ON operator_events(run_id,sequence);
            COMMIT;
            """)
            row = c.execute("SELECT value FROM schema_meta WHERE key='schema_version'").fetchone()
            if row is None:
                c.execute(
                    "INSERT INTO schema_meta(key,value) VALUES('schema_version',?)",
                    (str(SCHEMA_VERSION),),
                )
            elif int(row[0]) != SCHEMA_VERSION:
                raise OperatorError("unsupported_operator_schema")

    def _append_event_tx(self, c, run_id: str, event_type: str, payload: dict[str, Any]) -> int:
        cur = c.execute(
            "INSERT INTO operator_events(run_id,event_type,created_at,payload_json) VALUES(?,?,?,?)",
            (run_id, event_type, self._now(), _canonical_json(payload)),
        )
        return int(cur.lastrowid)

    def create_run(self, create_key: str) -> RunSnapshot:
        run_id = derive_run_id(create_key)
        now = self._now()
        with self._lock, self._connect() as c:
            try:
                c.execute("BEGIN IMMEDIATE")
                row = c.execute(
                    "SELECT run_id FROM operator_runs WHERE create_key=?",
                    (create_key,),
                ).fetchone()
                if row is None:
                    c.execute(
                        """INSERT INTO operator_runs(
                           run_id,create_key,state,current_attempt,source_hash,source_name,
                           canonical_job_id,created_at,updated_at
                           ) VALUES(?,?,?,?,?,?,?,?,?)""",
                        (run_id, create_key, "DRAFT", 0, None, None, None, now, now),
                    )
                    self._append_event_tx(c, run_id, "RUN_CREATED", {"state": "DRAFT"})
                elif row[0] != run_id:
                    raise OperatorConflict("create_key_identity_conflict")
                c.execute("COMMIT")
            except Exception:
                c.execute("ROLLBACK")
                raise
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> RunSnapshot:
        with self._connect() as c:
            row = c.execute(
                """SELECT run_id,state,current_attempt,source_hash,source_name,
                          canonical_job_id,created_at,updated_at
                   FROM operator_runs WHERE run_id=?""",
                (run_id,),
            ).fetchone()
        if row is None:
            raise OperatorError("run_not_found")
        return RunSnapshot(*row)

    def list_runs(self) -> tuple[RunSnapshot, ...]:
        with self._connect() as c:
            rows = c.execute(
                """SELECT run_id,state,current_attempt,source_hash,source_name,
                          canonical_job_id,created_at,updated_at
                   FROM operator_runs ORDER BY created_at,run_id"""
            ).fetchall()
        return tuple(RunSnapshot(*row) for row in rows)

    def bind_source_attempt(
        self,
        run_id: str,
        *,
        attempt: int,
        canonical_job_id: str,
        idempotency_key: str,
        source_hash: str,
        source_name: str,
        retry_of_job_id: str | None = None,
    ) -> RunSnapshot:
        if attempt < 1 or len(source_hash) != 64:
            raise OperatorError("invalid_attempt_binding")
        now = self._now()
        with self._lock, self._connect() as c:
            try:
                c.execute("BEGIN IMMEDIATE")
                run = c.execute(
                    "SELECT state,current_attempt,source_hash FROM operator_runs WHERE run_id=?",
                    (run_id,),
                ).fetchone()
                if run is None:
                    raise OperatorError("run_not_found")
                expected = 1 if run[1] == 0 else run[1] + 1
                if attempt != expected:
                    raise OperatorConflict("attempt_sequence_conflict")
                if run[1] == 0:
                    if run[0] != "DRAFT":
                        raise OperatorConflict("initial_import_requires_draft")
                else:
                    if run[0] != "FAILED":
                        raise OperatorConflict("retry_requires_failed_run")
                    if run[2] != source_hash:
                        raise OperatorConflict("retry_source_hash_conflict")
                c.execute(
                    """INSERT INTO operator_attempts(
                       run_id,attempt,canonical_job_id,idempotency_key,source_hash,
                       state,retry_of_job_id,created_at
                       ) VALUES(?,?,?,?,?,?,?,?)""",
                    (
                        run_id, attempt, canonical_job_id, idempotency_key, source_hash,
                        "READY", retry_of_job_id, now,
                    ),
                )
                c.execute(
                    """UPDATE operator_runs
                       SET state='READY',current_attempt=?,source_hash=?,source_name=?,
                           canonical_job_id=?,updated_at=?
                       WHERE run_id=?""",
                    (attempt, source_hash, source_name, canonical_job_id, now, run_id),
                )
                self._append_event_tx(
                    c,
                    run_id,
                    "SOURCE_BOUND" if attempt == 1 else "RETRY_BOUND",
                    {
                        "attempt": attempt,
                        "canonical_job_id": canonical_job_id,
                        "source_hash": source_hash,
                        "retry_of_job_id": retry_of_job_id,
                    },
                )
                c.execute("COMMIT")
            except Exception:
                c.execute("ROLLBACK")
                raise
        return self.get_run(run_id)

    def attempt(self, run_id: str, attempt: int | None = None) -> AttemptSnapshot:
        run = self.get_run(run_id)
        number = run.attempt if attempt is None else attempt
        if number < 1:
            raise OperatorError("attempt_not_found")
        with self._connect() as c:
            row = c.execute(
                """SELECT run_id,attempt,canonical_job_id,idempotency_key,source_hash,
                          state,retry_of_job_id,created_at
                   FROM operator_attempts WHERE run_id=? AND attempt=?""",
                (run_id, number),
            ).fetchone()
        if row is None:
            raise OperatorError("attempt_not_found")
        return AttemptSnapshot(*row)

    def record_event(
        self,
        run_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> OperatorEvent:
        if type(event_type) is not str or not event_type.strip():
            raise OperatorError("invalid_event_type")
        with self._lock, self._connect() as c:
            try:
                c.execute("BEGIN IMMEDIATE")
                if c.execute("SELECT 1 FROM operator_runs WHERE run_id=?", (run_id,)).fetchone() is None:
                    raise OperatorError("run_not_found")
                sequence = self._append_event_tx(c, run_id, event_type.strip(), dict(payload or {}))
                c.execute("UPDATE operator_runs SET updated_at=? WHERE run_id=?", (self._now(), run_id))
                c.execute("COMMIT")
            except Exception:
                c.execute("ROLLBACK")
                raise
        return next(e for e in self.events(run_id) if e.sequence == sequence)

    def transition(
        self,
        run_id: str,
        *,
        expected: set[str] | tuple[str, ...],
        target: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> RunSnapshot:
        if target not in SAFE_STATES:
            raise OperatorError("invalid_target_state")
        expected_set = set(expected)
        if not expected_set or not expected_set.issubset(SAFE_STATES):
            raise OperatorError("invalid_expected_state")
        now = self._now()
        with self._lock, self._connect() as c:
            try:
                c.execute("BEGIN IMMEDIATE")
                row = c.execute(
                    "SELECT state,current_attempt FROM operator_runs WHERE run_id=?",
                    (run_id,),
                ).fetchone()
                if row is None:
                    raise OperatorError("run_not_found")
                if row[0] not in expected_set:
                    raise OperatorConflict(f"state_conflict:{row[0]}")
                c.execute(
                    "UPDATE operator_runs SET state=?,updated_at=? WHERE run_id=?",
                    (target, now, run_id),
                )
                if row[1] > 0:
                    c.execute(
                        "UPDATE operator_attempts SET state=? WHERE run_id=? AND attempt=?",
                        (target, run_id, row[1]),
                    )
                self._append_event_tx(
                    c,
                    run_id,
                    event_type,
                    {"from": row[0], "to": target, **dict(payload or {})},
                )
                c.execute("COMMIT")
            except Exception:
                c.execute("ROLLBACK")
                raise
        return self.get_run(run_id)

    def record_observation(
        self,
        run_id: str,
        *,
        state: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> RunSnapshot:
        current = self.get_run(run_id)
        if current.state == state:
            return current
        allowed = {
            "READY": {"ACTIVE", "SUCCEEDED", "FAILED"},
            "ACTIVE": {"SUCCEEDED", "FAILED"},
        }
        if state not in allowed.get(current.state, set()):
            raise OperatorConflict(f"invalid_observed_transition:{current.state}->{state}")
        return self.transition(
            run_id,
            expected={current.state},
            target=state,
            event_type=event_type,
            payload=payload,
        )

    def events(self, run_id: str) -> tuple[OperatorEvent, ...]:
        self.get_run(run_id)
        with self._connect() as c:
            rows = c.execute(
                """SELECT sequence,run_id,event_type,created_at,payload_json
                   FROM operator_events WHERE run_id=? ORDER BY sequence""",
                (run_id,),
            ).fetchall()
        return tuple(
            OperatorEvent(row[0], row[1], row[2], row[3], json.loads(row[4]))
            for row in rows
        )

    def snapshot(self) -> dict[str, object]:
        runs = self.list_runs()
        return {
            "schema_version": SCHEMA_VERSION,
            "runs": [r.to_safe_dict() for r in runs],
            "events": {
                r.run_id: [e.to_safe_dict() for e in self.events(r.run_id)]
                for r in runs
            },
        }
