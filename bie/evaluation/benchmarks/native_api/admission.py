"""Operator-owned, single-host admission across campaigns using the SAME registry.

Reservations commit before native dispatch and are never automatically retried.
This provides at-most-once admission, not exactly-once distributed execution. A
DB administrator can rewrite the DB and its hash chain; protect this directory.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import os
import sqlite3
import stat
from urllib.parse import quote

from ..models import BenchmarkError, canonical_json, digest, digest_string, ident, strict_loads
from ..native_campaign.contracts import require
from ..native_campaign.runtime import private_directory

SCHEMA = 'bie.eval.api-admission/1'
STATES = {'RESERVED', 'FINISHED', 'BLOCKED'}


def context(scope_id: str, runtime_sha256: str, policy_sha256: str) -> dict:
    return dict(schema_version=SCHEMA, scope_id=ident(scope_id),
                runtime_sha256=digest_string(runtime_sha256),
                policy_sha256=digest_string(policy_sha256))


class Admission:
    """One operator-provisioned registry, never implicitly created by a run."""
    def __init__(self, path, configuration):
        require(type(configuration) is dict and set(configuration) ==
                {'schema_version', 'scope_id', 'runtime_sha256', 'policy_sha256'}, 'API_ADMISSION_CONTEXT')
        expected = context(configuration['scope_id'], configuration['runtime_sha256'], configuration['policy_sha256'])
        require(configuration == expected, 'API_ADMISSION_CONTEXT')
        self._context_json = canonical_json(expected)
        self.path = Path(path).absolute()
        self._paths()
        with self._tx() as db:
            self._verify(db)

    @property
    def configuration(self):
        return strict_loads(self._context_json)

    @classmethod
    def create(cls, path, configuration):
        # Validate configuration BEFORE creating any bytes.
        require(type(configuration) is dict, 'API_ADMISSION_CONTEXT')
        expected = context(configuration.get('scope_id'), configuration.get('runtime_sha256'),
                           configuration.get('policy_sha256'))
        require(configuration == expected, 'API_ADMISSION_CONTEXT')
        path = Path(path).absolute()
        private_directory(path.parent)
        for p in (path, *(Path(str(path)+s) for s in ('-wal','-shm','-journal'))):
            require(not p.exists() and not p.is_symlink(), 'API_ADMISSION_ALREADY_EXISTS')
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        db = sqlite3.connect('file:'+quote(str(path), safe='/')+'?mode=rw', uri=True, isolation_level=None)
        try:
            db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN IMMEDIATE')
            db.execute('CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT NOT NULL)')
            db.execute('CREATE TABLE attempts (effect TEXT PRIMARY KEY, plan TEXT NOT NULL, job TEXT NOT NULL, '
                       'state TEXT NOT NULL, result TEXT, reason TEXT)')
            db.execute('CREATE TABLE events (n INTEGER PRIMARY KEY, body TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL)')
            db.execute('INSERT INTO meta VALUES (?,?)', ('context', canonical_json(expected)))
            db.execute('COMMIT')
        except BaseException:
            if db.in_transaction:
                db.execute('ROLLBACK')
            raise
        finally:
            db.close()
        return cls(path, configuration)

    def _paths(self):
        private_directory(self.path.parent)
        for p in (self.path, *(Path(str(self.path)+s) for s in ('-wal','-shm','-journal'))):
            require(not p.is_symlink(), 'API_ADMISSION_SYMLINK')
            if p.exists():
                info = p.stat()
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'API_ADMISSION_FILE')
        require(self.path.is_file(), 'API_ADMISSION_MISSING')

    @contextmanager
    def _tx(self):
        self._paths()
        # mode=rw is essential: a deleted registry must not become a fresh budget.
        db = sqlite3.connect('file:'+quote(str(self.path), safe='/')+'?mode=rw', uri=True,
                             isolation_level=None, timeout=10)
        try:
            db.execute('PRAGMA trusted_schema=OFF')
            db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.execute('COMMIT')
        except BaseException:
            if db.in_transaction:
                db.execute('ROLLBACK')
            raise
        finally:
            db.close()

    @staticmethod
    def _projection(db):
        return digest([list(r) for r in db.execute('SELECT * FROM attempts ORDER BY effect')])

    def _verify(self, db, projection=True):
        objects = set(db.execute("SELECT type,name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"))
        require(objects == {('table','meta'), ('table','attempts'), ('table','events')}, 'API_ADMISSION_SCHEMA')
        require(list(db.execute('SELECT k,v FROM meta')) == [('context',self._context_json)], 'API_ADMISSION_CONTEXT_CHANGED')
        for effect, plan, job, state, result, reason in db.execute('SELECT * FROM attempts'):
            digest_string(effect); digest_string(plan); ident(job)
            require(state in STATES, 'API_ADMISSION_STATE')
            if result is not None:
                digest_string(result)
            require((state == 'RESERVED' and result is None and reason is None) or
                    (state == 'FINISHED' and result is not None and reason is None) or
                    (state == 'BLOCKED' and result is not None and type(reason) is str), 'API_ADMISSION_ROW')
        n, head, last = 0, '0'*64, None
        for row_number, body, previous, sha in db.execute('SELECT n,body,previous,hash FROM events ORDER BY n'):
            obj = strict_loads(body)
            require(row_number == n+1 and previous == head and
                    digest(dict(n=row_number, body=obj, previous=previous)) == sha, 'API_ADMISSION_CHAIN')
            require(type(obj) is dict and set(obj) == {'kind','effect','state_sha256'} and
                    obj['kind'] in ('RESERVE','FINISH','BLOCK'), 'API_ADMISSION_EVENT')
            digest_string(obj['effect']); digest_string(obj['state_sha256'])
            n, head, last = row_number, sha, obj
        if projection:
            require((last is not None and last['state_sha256'] == self._projection(db)) or
                    (last is None and not list(db.execute('SELECT effect FROM attempts'))), 'API_ADMISSION_PROJECTION')
        return n, head

    def _event(self, db, kind, effect):
        n, previous = self._verify(db, projection=False)
        body = dict(kind=kind, effect=effect, state_sha256=self._projection(db))
        sha = digest(dict(n=n+1, body=body, previous=previous))
        db.execute('INSERT INTO events VALUES(?,?,?,?)', (n+1,canonical_json(body),previous,sha))

    def reserve(self, effect: str, plan: str, job: str):
        digest_string(effect); digest_string(plan); ident(job)
        with self._tx() as db:
            self._verify(db)
            row = db.execute('SELECT plan,job,state,result,reason FROM attempts WHERE effect=?',(effect,)).fetchone()
            if row is not None:
                require(row[:2] == (plan,job), 'API_CROSS_CAMPAIGN_DUPLICATE')
                require(row[2] == 'FINISHED', 'API_ATTEMPT_UNAVAILABLE')
                return dict(replayed=True, result_sha256=row[3])
            db.execute('INSERT INTO attempts VALUES(?,?,?,?,NULL,NULL)',(effect,plan,job,'RESERVED'))
            self._event(db,'RESERVE',effect)
            return dict(replayed=False, result_sha256=None)

    def finish(self, effect, plan, job, result_sha256):
        self._terminal(effect, plan, job, result_sha256, None)

    def block(self, effect, plan, job, receipt_sha256, reason):
        ident(reason)
        self._terminal(effect, plan, job, receipt_sha256, reason)

    def _terminal(self, effect, plan, job, result_sha256, reason):
        digest_string(effect); digest_string(plan); ident(job); digest_string(result_sha256)
        with self._tx() as db:
            self._verify(db)
            row = db.execute('SELECT plan,job,state,result,reason FROM attempts WHERE effect=?',(effect,)).fetchone()
            require(row is not None and row[:2] == (plan,job), 'API_ADMISSION_BINDING')
            target = 'FINISHED' if reason is None else 'BLOCKED'
            if row[2] == target and row[3:] == (result_sha256,reason):
                return
            require(row[2] == 'RESERVED', 'API_ADMISSION_TERMINAL')
            db.execute('UPDATE attempts SET state=?,result=?,reason=? WHERE effect=?',
                       (target,result_sha256,reason,effect))
            self._event(db,'FINISH' if reason is None else 'BLOCK',effect)

    def snapshot(self):
        with self._tx() as db:
            count, head = self._verify(db)
            rows = [dict(zip(('effect','plan','job','state','result_sha256','reason'),r))
                    for r in db.execute('SELECT * FROM attempts ORDER BY effect')]
            return dict(schema_version=SCHEMA, configuration=self.configuration, attempts=rows,
                        event_count=count, chain_head=head, operator_owned_single_host=True,
                        distributed_authority=False, product_accepted=False)
