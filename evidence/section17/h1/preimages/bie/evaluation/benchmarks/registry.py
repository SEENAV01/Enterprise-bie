"""Durable case registry. BIE-EVAL-REG-001; local single-operator trust domain.

This is not an authentication service. Keep the database/evaluator process out
of candidate-worker access. SQL integrity is not protection against its owner.
"""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator
from .models import BenchmarkCase, BenchmarkError, canonical_json, digest, ident, strict_loads

SCHEMA_VERSION = 1

class Registry:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.connection = sqlite3.connect(self.path, timeout=10,
            isolation_level=None, autocommit=sqlite3.LEGACY_TRANSACTION_CONTROL)
        self.connection.row_factory = sqlite3.Row
        try:
            self.connection.execute("PRAGMA foreign_keys=ON")
            current = self.connection.execute("PRAGMA user_version").fetchone()[0]
            if current not in (0, SCHEMA_VERSION):
                raise BenchmarkError("UNSUPPORTED_DATABASE_VERSION")
            with self.transaction():
                self.connection.execute("""CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY, task_id TEXT NOT NULL,
                    content_sha TEXT NOT NULL, body TEXT NOT NULL)""")
                self.connection.execute("""CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL,
                    previous_sha TEXT NOT NULL, event_sha TEXT NOT NULL)""")
                self.connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        except Exception:
            self.connection.close()
            raise

    def __enter__(self) -> Registry:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        if self.connection.in_transaction:
            raise BenchmarkError("NESTED_TRANSACTION")
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.connection.execute("COMMIT")
        except BaseException:
            self.connection.execute("ROLLBACK")
            raise

    def _event(self, kind: str, body: dict) -> None:
        row = self.connection.execute("SELECT seq,event_sha FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        seq, previous = (row["seq"] + 1, row["event_sha"]) if row else (1, "0" * 64)
        event = {"seq": seq, "kind": kind, "body": body, "previous_sha": previous}
        self.connection.execute("INSERT INTO events VALUES (?,?,?,?,?)",
            (seq, kind, canonical_json(body), previous, digest(event)))

    def audit_head(self) -> str:
        previous = "0" * 64
        for seq, row in enumerate(self.connection.execute("SELECT * FROM events ORDER BY seq"), 1):
            event = {"seq": row["seq"], "kind": row["kind"], "body": strict_loads(row["body"]),
                     "previous_sha": row["previous_sha"]}
            if row["seq"] != seq or row["previous_sha"] != previous or digest(event) != row["event_sha"]:
                raise BenchmarkError("EVENT_CHAIN_TAMPERED")
            previous = row["event_sha"]
        return previous

    def register(self, cases: list[BenchmarkCase]) -> tuple[str, ...]:
        if type(cases) is not list or not 1 <= len(cases) <= 10000:
            raise BenchmarkError("INVALID_CASE_BATCH")
        if any(type(c) is not BenchmarkCase for c in cases):
            raise BenchmarkError("INVALID_CASE_TYPE")
        if len({c.case_id for c in cases}) != len(cases):
            raise BenchmarkError("DUPLICATE_CASE_ID")
        with self.transaction():
            for c in cases:
                existing = self.connection.execute("SELECT content_sha FROM cases WHERE case_id=?", (c.case_id,)).fetchone()
                if existing:
                    raise BenchmarkError("CASE_ALREADY_REGISTERED", c.case_id)
                self.connection.execute("INSERT INTO cases VALUES (?,?,?,?)", (
                    c.case_id, c.task_id, c.content_sha256, canonical_json(c.to_dict())))
            self._event("REGISTER_CASES", {"cases": sorted(c.content_sha256 for c in cases)})
        return tuple(c.case_id for c in cases)

    def get_case(self, case_id: str) -> BenchmarkCase:
        ident(case_id)
        row = self.connection.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
        if row is None:
            raise BenchmarkError("CASE_NOT_FOUND", case_id)
        case = BenchmarkCase.from_dict(strict_loads(row["body"]))
        if case.case_id != row["case_id"] or case.task_id != row["task_id"] or case.content_sha256 != row["content_sha"]:
            raise BenchmarkError("CASE_CONTENT_TAMPERED")
        return case

    def all_cases(self, task_id: str | None = None) -> tuple[BenchmarkCase, ...]:
        if task_id is not None:
            ident(task_id)
            rows = self.connection.execute("SELECT case_id FROM cases WHERE task_id=? ORDER BY case_id", (task_id,))
        else:
            rows = self.connection.execute("SELECT case_id FROM cases ORDER BY case_id")
        return tuple(self.get_case(row["case_id"]) for row in rows.fetchall())

    def inventory(self) -> tuple[dict, ...]:
        return tuple({"case_id": c.case_id, "task_id": c.task_id, "sha256": c.content_sha256,
                      "domain": c.domain, "split": c.split, "evidence_grade": c.evidence_grade}
                     for c in self.all_cases())
