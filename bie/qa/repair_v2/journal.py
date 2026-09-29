"""Durable local attempt budget with serialized claims and an integrity chain.

Private operator-owned storage is required. Hash chaining detects accidental edits,
not a privileged attacker able to rewrite the entire database. No crash auto-retry:
an unfinished reservation requires explicit operator investigation.
"""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import os,sqlite3,stat,json
from ..release_v2.contracts import ContractError,canonical_bytes,digest,integer

class Journal:
    def __init__(self,path,snapshot,policy):
        self.path=Path(path);self.snapshot=snapshot;self.policy=policy
        if not self.path.parent.is_dir() or self.path.parent.is_symlink():raise ContractError('REPAIR_JOURNAL_DIRECTORY')
        if self.path.exists() or self.path.is_symlink():
            st=self.path.lstat()
            if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1:raise ContractError('REPAIR_JOURNAL_FILE')
        else:
            fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600);os.close(fd)
        self._fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW)
        st=os.fstat(self._fd);self._identity=(st.st_dev,st.st_ino)
        self.binding=dict(run_id=snapshot.run_id,revision=snapshot.revision,snapshot_digest=snapshot.content_digest,policy_digest=policy.content_digest)
        with self.connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS metadata (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, body TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL)')
            row=db.execute('SELECT body FROM metadata WHERE id=1').fetchone()
            data=canonical_bytes(self.binding).decode()
            if row is None:db.execute('INSERT INTO metadata VALUES(1,?)',(data,))
            elif row[0]!=data:raise ContractError('REPAIR_JOURNAL_BINDING')
            self._read(db)

    def close(self):
        fd=getattr(self,'_fd',None)
        if fd is not None:os.close(fd);self._fd=None

    def __del__(self):
        self.close()

    @contextmanager
    def connection(self):
        if getattr(self,'_fd',None) is None:raise ContractError('REPAIR_JOURNAL_CLOSED')
        st=self.path.lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1 or (st.st_dev,st.st_ino)!=self._identity or self.path.parent.is_symlink():raise ContractError('REPAIR_JOURNAL_FILE_CHANGED')
        db=sqlite3.connect(str(self.path),timeout=5,isolation_level=None)
        try:
            db.execute('PRAGMA synchronous=FULL');db.execute('BEGIN IMMEDIATE')
            yield db
            db.execute('COMMIT')
        except Exception:
            if db.in_transaction:db.execute('ROLLBACK')
            raise
        finally:db.close()

    def _read(self,db):
        binding=db.execute('SELECT body FROM metadata WHERE id=1').fetchone()
        if binding is None or binding[0]!=canonical_bytes(self.binding).decode():raise ContractError('REPAIR_JOURNAL_BINDING')
        head=digest(self.binding);rows=[];pending={}
        for expected,(seq,body,previous,h) in enumerate(db.execute('SELECT seq,body,previous,hash FROM events ORDER BY seq'),1):
            try:obj=json.loads(body)
            except (ValueError,TypeError) as e:raise ContractError('REPAIR_JOURNAL_CORRUPT') from e
            if seq!=expected or previous!=head or body!=canonical_bytes(obj).decode() or digest(dict(seq=seq,body=obj,previous=previous))!=h:raise ContractError('REPAIR_JOURNAL_CORRUPT')
            if obj.get('kind')=='RESERVED':
                if obj['attempt'] in pending:raise ContractError('REPAIR_JOURNAL_CORRUPT')
                pending[obj['attempt']]=True
            elif obj.get('kind')=='FINISHED':
                if not pending.get(obj['attempt']):raise ContractError('REPAIR_JOURNAL_CORRUPT')
                pending[obj['attempt']]=False
            else:raise ContractError('REPAIR_JOURNAL_CORRUPT')
            rows.append(obj);head=h
        return rows,head

    def _append(self,db,obj):
        rows,head=self._read(db);n=len(rows)+1;h=digest(dict(seq=n,body=obj,previous=head))
        db.execute('INSERT INTO events VALUES(?,?,?,?)',(n,canonical_bytes(obj).decode(),head,h));return h

    def reserve(self,proposal,now):
        integer(now,'now')
        if proposal.base_digest!=self.snapshot.content_digest or proposal.policy_digest!=self.policy.content_digest:raise ContractError('REPAIR_JOURNAL_PROPOSAL_BINDING')
        size=sum(x.artifact.size for x in proposal.replacements)
        with self.connection() as db:
            rows,head=self._read(db);claims=[r for r in rows if r['kind']=='RESERVED'];ends=[r for r in rows if r['kind']=='FINISHED']
            if any(r['status']=='STAGED_FOR_REVIEW' for r in ends):raise ContractError('REPAIR_SESSION_ALREADY_STAGED')
            if any(r['attempt'] not in {e['attempt'] for e in ends} for r in claims):raise ContractError('REPAIR_PENDING_ATTEMPT_MANUAL_REVIEW')
            if any(r['proposal_id']==proposal.proposal_id for r in claims):raise ContractError('REPAIR_DUPLICATE_PROPOSAL')
            if any(r['effect_digest']==proposal.effect_digest for r in claims):raise ContractError('REPAIR_REPEATED_EFFECT')
            if len(claims)>=self.policy.max_attempts:raise ContractError('REPAIR_ATTEMPT_BUDGET')
            if size+sum(r['reserved_bytes'] for r in claims)>self.policy.max_total_replacement_bytes:raise ContractError('REPAIR_TOTAL_BYTE_BUDGET')
            if (len(claims)+1)*self.policy.worker_timeout_seconds>self.policy.max_total_worker_seconds:raise ContractError('REPAIR_TOTAL_TIME_BUDGET')
            if claims and now<claims[-1]['reserved_at']:raise ContractError('REPAIR_CLOCK_ROLLBACK')
            n=len(claims)+1
            self._append(db,dict(kind='RESERVED',attempt=n,proposal_id=proposal.proposal_id,proposal_digest=proposal.content_digest,effect_digest=proposal.effect_digest,reserved_at=now,reserved_bytes=size,reserved_seconds=self.policy.worker_timeout_seconds))
            return n

    def finish(self,attempt,status,receipt_digest):
        from ..release_v2.contracts import choice,sha256
        integer(attempt,'attempt',1,20);choice(status,('REJECTED','STAGED_FOR_REVIEW'),'status');sha256(receipt_digest,'receipt_digest')
        with self.connection() as db:
            rows,_=self._read(db)
            if not any(r['kind']=='RESERVED' and r['attempt']==attempt for r in rows) or any(r['kind']=='FINISHED' and r['attempt']==attempt for r in rows):raise ContractError('REPAIR_ATTEMPT_TRANSITION')
            return self._append(db,dict(kind='FINISHED',attempt=attempt,status=status,receipt_digest=receipt_digest))

    def export(self):
        with self.connection() as db:
            rows,head=self._read(db)
            return dict(binding=self.binding,events=rows,chain_head=head,product_accepted=False)
