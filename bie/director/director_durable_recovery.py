"""Durable artifact index and fenced DIR worker leases using SQLite + CAS."""
from dataclasses import asdict,dataclass
import sqlite3
import time

from bie.infrastructure.artifact_store import ArtifactCatalog,ArtifactRecord,BlobRef,ArtifactStoreError
from bie.infrastructure.idempotency_store import Claim,SQLiteIdempotencyStore,IdempotencyError
from .contract_validation import finite,nonblank
from .director_artifacts import canonical,fields,parse_json


class RecoveryError(RuntimeError):pass


def _record_json(record):return canonical(asdict(record))


def _record(value):
    fields(value,ArtifactRecord.__dataclass_fields__,'durable artifact record')
    fields(value['blob'],BlobRef.__dataclass_fields__,'durable blob reference')
    if type(value['parent_artifact_ids']) is not list or type(value['metadata']) is not dict:raise ArtifactStoreError('durable record collection mismatch')
    return ArtifactRecord(**{**value,'blob':BlobRef(**value['blob'])})


class SQLiteArtifactCatalog(ArtifactCatalog):
    """Journal every immutable ArtifactRecord; payload bytes remain in CAS."""
    def __init__(self,cas,path):
        super().__init__(cas);self.path=str(path);self.db=sqlite3.connect(path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('''CREATE TABLE IF NOT EXISTS artifact_records(
            artifact_id TEXT PRIMARY KEY,record_json TEXT NOT NULL,created REAL NOT NULL)''');self.db.commit()
        pending={row[0]:_record(parse_json(row[1])) for row in self.db.execute('SELECT artifact_id,record_json FROM artifact_records')}
        while pending:
            ready=[aid for aid,row in pending.items() if set(row.parent_artifact_ids)<=self.records.keys()]
            if not ready:raise ArtifactStoreError('durable artifact index has missing parent or cycle')
            for aid in sorted(ready):
                record=pending.pop(aid)
                if aid!=record.artifact_id:raise ArtifactStoreError('durable artifact key mismatch')
                super().register(record)

    def register(self,record):
        record.validate();text=_record_json(record)
        existing=self.db.execute('SELECT record_json FROM artifact_records WHERE artifact_id=?',(record.artifact_id,)).fetchone()
        if existing is not None:
            if existing[0]!=text:raise ArtifactStoreError('durable artifact id collision')
            return super().register(record)
        with self.db:
            self.db.execute('INSERT INTO artifact_records VALUES(?,?,?)',(record.artifact_id,text,time.time()))
            super().register(record)

    def verify_durable_index(self):
        rows=self.db.execute('SELECT artifact_id,record_json FROM artifact_records ORDER BY artifact_id').fetchall();problems=[]
        if len(rows)!=len(self.records):problems.append('RECORD_COUNT_MISMATCH')
        for aid,text in rows:
            try:record=_record(parse_json(text))
            except Exception:problems.append(aid+':INVALID_RECORD');continue
            if self.records.get(aid)!=record:problems.append(aid+':MEMORY_INDEX_MISMATCH')
            elif not self.cas.exists(record.blob):problems.append(aid+':CAS_MISSING_OR_CORRUPT')
        return tuple(sorted(problems))

    def close(self):self.db.close()


@dataclass(frozen=True)
class FencedLease:
    key:str
    fingerprint:str
    owner:str
    epoch:int
    state:str
    expires_at:float
    result_ref:str|None


class DirectorLeaseStore:
    def __init__(self,path):
        self.db=sqlite3.connect(path);self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('''CREATE TABLE IF NOT EXISTS director_leases(
            key TEXT PRIMARY KEY,fingerprint TEXT NOT NULL,owner TEXT NOT NULL,epoch INTEGER NOT NULL,
            state TEXT NOT NULL,expires_at REAL NOT NULL,result_ref TEXT)''');self.db.commit()

    def get(self,key):
        row=self.db.execute('SELECT * FROM director_leases WHERE key=?',(key,)).fetchone()
        if row is None:raise RecoveryError('unknown director lease')
        return FencedLease(*row)

    def acquire(self,key,fingerprint,owner,*,now=None,ttl_seconds=60):
        for value in (key,fingerprint,owner):nonblank(value,'lease identity')
        if type(ttl_seconds) is not int or not 1<=ttl_seconds<=3600:raise RecoveryError('bounded lease TTL required')
        now=time.time() if now is None else finite(now,'lease time',low=0);expires=now+ttl_seconds
        with self.db:
            self.db.execute('BEGIN IMMEDIATE');row=self.db.execute('SELECT * FROM director_leases WHERE key=?',(key,)).fetchone()
            if row is None:
                self.db.execute('INSERT INTO director_leases VALUES(?,?,?,?,?,?,?)',(key,fingerprint,owner,1,'ACTIVE',expires,None))
            else:
                prior=FencedLease(*row)
                if prior.fingerprint!=fingerprint:raise RecoveryError('lease fingerprint conflict')
                if prior.state=='COMPLETED':return prior
                if prior.state=='ACTIVE' and prior.expires_at>now and prior.owner!=owner:raise RecoveryError('director lease held by another live worker')
                epoch=prior.epoch if prior.owner==owner and prior.expires_at>now else prior.epoch+1
                self.db.execute('UPDATE director_leases SET owner=?,epoch=?,state=?,expires_at=?,result_ref=NULL WHERE key=?',
                    (owner,epoch,'ACTIVE',expires,key))
        return self.get(key)

    def _active(self,lease,now):
        current=self.get(lease.key)
        if current!=lease or current.state!='ACTIVE' or current.expires_at<now:raise RecoveryError('stale, expired or superseded lease fence')
        return current

    def heartbeat(self,lease,*,now=None,ttl_seconds=60):
        now=time.time() if now is None else finite(now,'lease time',low=0)
        if type(ttl_seconds) is not int or not 1<=ttl_seconds<=3600:raise RecoveryError('bounded lease TTL required')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE');self._active(lease,now)
            self.db.execute('UPDATE director_leases SET expires_at=? WHERE key=?',(now+ttl_seconds,lease.key))
        return self.get(lease.key)

    def assert_active(self,lease,*,now=None):
        now=time.time() if now is None else finite(now,'lease time',low=0)
        return self._active(lease,now)

    def complete(self,lease,result_ref,*,now=None):
        nonblank(result_ref,'lease result reference');now=time.time() if now is None else finite(now,'lease time',low=0)
        current=self.get(lease.key)
        if current.state=='COMPLETED':
            if current.fingerprint!=lease.fingerprint or current.result_ref!=result_ref:raise RecoveryError('completed lease result conflict')
            return current
        with self.db:
            self.db.execute('BEGIN IMMEDIATE');self._active(lease,now)
            self.db.execute("UPDATE director_leases SET state='COMPLETED',result_ref=?,expires_at=? WHERE key=?",
                (result_ref,now,lease.key))
        return self.get(lease.key)

    def reclaim_idempotency(self,store,lease,new_owner,*,now=None):
        if not isinstance(store,SQLiteIdempotencyStore):raise RecoveryError('SQLite idempotency store required')
        now=time.time() if now is None else finite(now,'lease time',low=0);current=self._active(lease,now)
        if current.owner!=new_owner or current.epoch<2:raise RecoveryError('new fenced owner required for abandoned claim')
        with store.db:
            store.db.execute('BEGIN IMMEDIATE')
            row=store.db.execute('SELECT key,fingerprint,state,owner,result_ref FROM claims WHERE key=?',(lease.key,)).fetchone()
            if row is None:raise IdempotencyError('unknown abandoned claim')
            claim=Claim(*row)
            if claim.fingerprint!=lease.fingerprint or claim.state!='CLAIMED':raise IdempotencyError('only matching incomplete claim can be reclaimed')
            store.db.execute('UPDATE claims SET owner=?,updated=? WHERE key=?',(new_owner,now,lease.key))
        return store.get(lease.key)

    def close(self):self.db.close()


class DirectorRecoveryCoordinator:
    def __init__(self,leases,ttl_seconds=60):
        if not isinstance(leases,DirectorLeaseStore):raise ValueError('DirectorLeaseStore required')
        if type(ttl_seconds) is not int or not 1<=ttl_seconds<=3600:raise ValueError('bounded recovery TTL required')
        self.leases=leases;self.ttl_seconds=ttl_seconds

    def acquire(self,key,fingerprint,owner):return self.leases.acquire(key,fingerprint,owner,ttl_seconds=self.ttl_seconds)
    def heartbeat(self,lease):return self.leases.heartbeat(lease,ttl_seconds=self.ttl_seconds)
    def assert_active(self,lease):return self.leases.assert_active(lease)
    def reclaim_claim(self,store,lease,owner):return self.leases.reclaim_idempotency(store,lease,owner)
    def complete(self,lease,result_ref):return self.leases.complete(lease,result_ref)
    def descriptor(self):return {'schema_version':'bie.dir.durable_recovery/1.0.0','ttl_seconds':self.ttl_seconds}
