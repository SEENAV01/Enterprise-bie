"""HARD029: local SQLite fencing, durable attempt budgets and transactional outbox.

A lease expiry is NOT proof that a former worker stopped. Old fencing tokens cannot
commit, and retries consume another attempt. Outbox receipts are not deployments.
Use a private trusted directory; hash chains are not protection from a DB administrator.
"""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass,asdict
from pathlib import Path
import sqlite3,os,time
from .common import *

@dataclass(frozen=True)
class LeasePolicy:
    attempts:int=3
    lease_seconds:int=60
    def __post_init__(self):
        integer(self.attempts,'attempts',1,100);integer(self.lease_seconds,'lease',1,3600)
    @property
    def content_digest(self):return digest(asdict(self))

class LeaseJournal:
    def __init__(self,path,binding,policy=LeasePolicy()):
        self.path=Path(path);self.binding=binding;self.policy=policy
        require(type(binding) is Binding and type(policy) is LeasePolicy,'H6_JOURNAL_TYPE')
        require(binding.policy_digest==policy.content_digest,'H6_JOURNAL_BINDING')
        require(self.path.parent.is_dir() and not self.path.is_symlink(),'H6_JOURNAL_PATH')
        for p in (self.path.parent,)+tuple(self.path.parent.parents):require(not p.is_symlink(),'H6_JOURNAL_PARENT_LINK')
        require(not self.path.exists() or self.path.is_file(),'H6_JOURNAL_FILE')
        with self.tx() as db:
            db.execute('CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY,v TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,effect TEXT UNIQUE NOT NULL,state TEXT NOT NULL,token INTEGER NOT NULL,attempt INTEGER NOT NULL,owner TEXT NOT NULL,lease INTEGER NOT NULL,last_clock INTEGER NOT NULL,result TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS events(n INTEGER PRIMARY KEY,body TEXT NOT NULL,prev TEXT NOT NULL,hash TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY,payload TEXT NOT NULL,payload_hash TEXT NOT NULL,acked INTEGER NOT NULL DEFAULT 0)')
            expected=canonical_bytes(dict(binding=asdict(binding),policy=asdict(policy))).decode()
            row=db.execute("SELECT v FROM meta WHERE k='binding'").fetchone()
            if row:require(row[0]==expected,'H6_JOURNAL_CONTEXT_CHANGED')
            else:db.execute("INSERT INTO meta VALUES('binding',?)",(expected,))
            self._verify(db)
        os.chmod(self.path,0o600)
    @contextmanager
    def tx(self):
        require(not self.path.is_symlink(),'H6_JOURNAL_LINK')
        db=sqlite3.connect(self.path,timeout=10,isolation_level=None)
        try:
            db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN IMMEDIATE');yield db;db.execute('COMMIT')
        except BaseException:
            if db.in_transaction:db.execute('ROLLBACK')
            raise
        finally:db.close()
    def _projection(self,db):
        return digest(dict(jobs=list(db.execute("SELECT * FROM jobs ORDER BY id")),outbox=list(db.execute("SELECT * FROM outbox ORDER BY id"))))
    def _verify(self,db,check_projection=True):
        head='0'*64;count=0;last=None
        for n,body,prev,h in db.execute('SELECT n,body,prev,hash FROM events ORDER BY n'):
            require(n==count+1 and prev==head and digest(dict(n=n,body=strict_json(body.encode()),previous=prev))==h,'H6_JOURNAL_CHAIN')
            head=h;count=n;last=strict_json(body.encode())
        if check_projection:
            current=self._projection(db)
            if last is not None:require(last['state_digest']==current,'H6_JOURNAL_STATE_CHANGED')
            else:require(not list(db.execute('SELECT id FROM jobs')) and not list(db.execute('SELECT id FROM outbox')),'H6_JOURNAL_EVENT_MISSING')
        return count,head
    def _event(self,db,body):
        n,head=self._verify(db,False);n+=1;body={**body,'state_digest':self._projection(db)};h=digest(dict(n=n,body=body,previous=head))
        db.execute('INSERT INTO events VALUES(?,?,?,?)',(n,canonical_bytes(body).decode(),head,h))
        return h
    def claim(self,job_id,effect_digest,owner,now):
        token(job_id,'job');sha256(effect_digest,'effect');token(owner,'owner');integer(now,'now')
        with self.tx() as db:
            self._verify(db)
            row=db.execute('SELECT effect,state,token,attempt,owner,lease,last_clock,result FROM jobs WHERE id=?',(job_id,)).fetchone()
            other=db.execute('SELECT id FROM jobs WHERE effect=?',(effect_digest,)).fetchone()
            require(other is None or other[0]==job_id,'H6_EFFECT_ALIAS')
            if row:
                effect,state,tok,attempt,old_owner,lease,last_clock,stored=row
                require(effect==effect_digest,'H6_JOB_EFFECT_CHANGED');require(now>=last_clock,'H6_CLOCK_ROLLBACK')
                if state=='FINISHED':return dict(job_id=job_id,state=state,token=tok,replayed=True,result_digest=stored)
                require(state!='CANCELLED','H6_JOB_CANCELLED')
                require(state!='RUNNING' or now>=lease,'H6_LEASE_BUSY')
                require(attempt<self.policy.attempts,'H6_ATTEMPT_BUDGET')
                tok+=1;attempt+=1
                db.execute('UPDATE jobs SET state=?,token=?,attempt=?,owner=?,lease=?,last_clock=? WHERE id=?',('RUNNING',tok,attempt,owner,now+self.policy.lease_seconds,now,job_id))
            else:
                tok=1;attempt=1
                db.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,NULL)',(job_id,effect_digest,'RUNNING',tok,attempt,owner,now+self.policy.lease_seconds,now))
            self._event(db,dict(kind='CLAIM',job_id=job_id,effect=effect_digest,token=tok,attempt=attempt,owner=owner,at=now))
            return dict(job_id=job_id,state='RUNNING',token=tok,attempt=attempt,lease_until=now+self.policy.lease_seconds,replayed=False)
    def _active(self,db,job_id,tok,owner,now):
        self._verify(db)
        row=db.execute('SELECT state,token,owner,lease,last_clock FROM jobs WHERE id=?',(job_id,)).fetchone()
        require(row is not None,'H6_JOB_UNKNOWN')
        state,current,principal,lease,last=row
        require(type(tok) is int and tok==current and owner==principal and state=='RUNNING','H6_STALE_FENCE')
        require(now>=last,'H6_CLOCK_ROLLBACK');require(now<lease,'H6_LEASE_EXPIRED')
    def heartbeat(self,job_id,tok,owner,now):
        integer(now,'now')
        with self.tx() as db:
            self._active(db,job_id,tok,owner,now)
            db.execute('UPDATE jobs SET lease=?,last_clock=? WHERE id=?',(now+self.policy.lease_seconds,now,job_id))
            self._event(db,dict(kind='HEARTBEAT',job_id=job_id,token=tok,at=now))
    def finish(self,job_id,tok,owner,now,result_digest,invalidations):
        integer(now,'now');sha256(result_digest,'result');ids(invalidations,'invalidations')
        with self.tx() as db:
            self._active(db,job_id,tok,owner,now)
            payload=dict(job_id=job_id,token=tok,result_digest=result_digest,invalidated=list(sorted(invalidations)),product_accepted=False)
            db.execute('INSERT INTO outbox VALUES(?,?,?,0)',(job_id,canonical_bytes(payload).decode(),digest(payload)))
            db.execute('UPDATE jobs SET state=?,result=?,last_clock=? WHERE id=?',('FINISHED',result_digest,now,job_id))
            self._event(db,dict(kind='FINISH',job_id=job_id,token=tok,at=now,result_digest=result_digest))
            return payload
    def cancel(self,job_id,now):
        integer(now,'now')
        with self.tx() as db:
            self._verify(db)
            row=db.execute('SELECT state,last_clock FROM jobs WHERE id=?',(job_id,)).fetchone()
            require(row is not None and row[0]!='FINISHED','H6_CANCEL_STATE');require(now>=row[1],'H6_CLOCK_ROLLBACK')
            db.execute("UPDATE jobs SET state='CANCELLED',token=token+1,last_clock=? WHERE id=?",(now,job_id))
            self._event(db,dict(kind='CANCEL',job_id=job_id,at=now))
    def pending(self):
        with self.tx() as db:
            self._verify(db);out=[]
            for k,p,h in db.execute('SELECT id,payload,payload_hash FROM outbox WHERE acked=0 ORDER BY id'):
                obj=strict_json(p.encode());require(digest(obj)==h,'H6_OUTBOX_CHANGED');out.append(obj)
            return out
    def acknowledge(self,job_id,payload_digest):
        sha256(payload_digest,'outbox digest')
        with self.tx() as db:
            self._verify(db)
            row=db.execute('SELECT payload,payload_hash,acked FROM outbox WHERE id=?',(job_id,)).fetchone()
            require(row is not None and row[1]==payload_digest and digest(strict_json(row[0].encode()))==row[1],'H6_OUTBOX_ACK_IDENTITY')
            if not row[2]:
                db.execute('UPDATE outbox SET acked=1 WHERE id=?',(job_id,));self._event(db,dict(kind='ACK',job_id=job_id,payload_digest=payload_digest))
    def export(self):
        with self.tx() as db:
            count,head=self._verify(db)
            return dict(binding=asdict(self.binding),events=[strict_json(r[0].encode()) for r in db.execute('SELECT body FROM events ORDER BY n')],chain_head=head,event_count=count,
              jobs=[dict(zip(('job_id','effect_digest','state','token','attempts','owner','lease','last_clock','result_digest'),r)) for r in db.execute('SELECT * FROM jobs ORDER BY id')],
              distributed_durability_verified=False,publication_performed=False,product_accepted=False)


def native_invalidations(graph,statuses,changed,reason):
    """Execute native invalidate() on the exact descendant closure; no registry write."""
    from ...infrastructure.task_invalidation import invalidate
    require(type(graph) is dict and graph and set(graph)==set(statuses),'H6_INVALIDATION_CENSUS')
    ids(tuple(graph),'graph');ids(changed,'changed');require(set(changed)<=set(graph),'H6_INVALIDATION_UNKNOWN_TASK')
    text(reason,'reason',1024)
    for k,deps in graph.items():
        ids(deps,'dependencies',minimum=0);require(set(deps)<=set(graph),'H6_INVALIDATION_DEPENDENCY')
        require(statuses[k] in ('PLANNED','RUNNING','IMPLEMENTED','VERIFIED','FAILED','INVALIDATED'),'H6_INVALIDATION_STATUS')
    done=set()
    while len(done)<len(graph):
        ready={k for k,d in graph.items() if k not in done and set(d)<=done}
        require(bool(ready),'H6_INVALIDATION_CYCLE');done|=ready
    # Preserve the actual triggering roots, including converging repairs. A single
    # source_task_id cannot truthfully represent two independent upstream changes.
    causes={k:({k} if k in changed else set()) for k in graph}
    while True:
        updated={k:causes[k].union(*(causes[d] for d in deps)) for k,deps in graph.items()}
        if updated==causes:break
        causes=updated
    affected={k for k,v in causes.items() if v}
    rows=[]
    for k in sorted(affected):
        roots=sorted(causes[k]);single=roots[0] if len(roots)==1 else None
        if statuses[k]=='INVALIDATED':rows.append(dict(task_id=k,previous_status='INVALIDATED',reason=reason,source_task_id=single,source_task_ids=roots,already_invalidated=True))
        else:rows.append(dict(asdict(invalidate(k,statuses[k],reason,single)),source_task_ids=roots,already_invalidated=False))
    return dict(invalidations=rows,affected_task_ids=sorted(affected),dispatch_performed=False,repository_modified=False,
        native_contract='bie.infrastructure.task_invalidation.invalidate',product_accepted=False)
