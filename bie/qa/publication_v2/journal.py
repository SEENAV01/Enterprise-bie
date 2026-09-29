"""Local transactional publication journal, in a PRIVATE operator-owned directory.

Not a distributed release ledger. No network, secret discovery or deployment.
Deleting/rolling back this private database defeats its local replay history;
production needs external append-only storage, backup and access controls.
"""
from __future__ import annotations
from pathlib import Path
import os,sqlite3,stat,hashlib
from contextlib import contextmanager
from ..release_v2.contracts import ContractError,canonical_bytes,token,integer
from .contracts import strict_json

class ReleaseJournal:
    def __init__(self,path:str|Path):
        p=Path(path).absolute()
        if p!=p.resolve() or not p.parent.is_dir():raise ContractError('JOURNAL_PATH')
        st=p.parent.stat()
        if st.st_uid!=os.geteuid() or st.st_mode&0o077:raise ContractError('JOURNAL_PRIVATE_DIRECTORY_REQUIRED')
        try:
            fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600);os.close(fd)
        except FileExistsError:pass
        st=p.lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1 or st.st_uid!=os.geteuid() or st.st_mode&0o077:
            raise ContractError('JOURNAL_UNSAFE_FILE')
        self.path=p
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS certificates (release_id TEXT, release_version TEXT, environment_id TEXT, digest TEXT UNIQUE NOT NULL, payload BLOB NOT NULL, PRIMARY KEY(release_id,release_version,environment_id))')
            db.execute('CREATE TABLE IF NOT EXISTS revocations (digest TEXT PRIMARY KEY, reason TEXT NOT NULL, revoked_at INTEGER NOT NULL)')
    @contextmanager
    def _db(self):
        db=sqlite3.connect(str(self.path),timeout=5,isolation_level='IMMEDIATE')
        try:
            db.execute('PRAGMA synchronous=FULL')
            with db:yield db
        finally:db.close()
    def record(self,certificate):
        payload=canonical_bytes(certificate);ident=hashlib.sha256(payload).hexdigest()
        key=tuple(certificate[x] for x in ('release_id','release_version','environment_id'))
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT digest,payload FROM certificates WHERE release_id=? AND release_version=? AND environment_id=?',key).fetchone()
            if row:
                if row[0]!=ident or bytes(row[1])!=payload:raise ContractError('PUBLICATION_VERSION_CONFLICT')
                if db.execute('SELECT 1 FROM revocations WHERE digest=?',(ident,)).fetchone():raise ContractError('CERTIFICATE_REVOKED')
                return ident,False
            db.execute('INSERT INTO certificates VALUES (?,?,?,?,?)',(*key,ident,payload))
        return ident,True
    def check(self,certificate):
        payload=canonical_bytes(certificate);ident=hashlib.sha256(payload).hexdigest()
        with self._db() as db:
            row=db.execute('SELECT payload FROM certificates WHERE digest=?',(ident,)).fetchone()
            if not row or bytes(row[0])!=payload:raise ContractError('CERTIFICATE_NOT_JOURNALED')
            if db.execute('SELECT 1 FROM revocations WHERE digest=?',(ident,)).fetchone():raise ContractError('CERTIFICATE_REVOKED')
        return ident
    def revoke(self,certificate,*,reason:str,as_of:int):
        # Explicit operator action only. This is intentionally NOT on the read-only CLI.
        token(reason,'reason');integer(as_of,'as_of');ident=self.check(certificate)
        if as_of<certificate['issued_at']:raise ContractError('REVOCATION_BEFORE_ISSUE')
        with self._db() as db:
            db.execute('INSERT INTO revocations VALUES (?,?,?)',(ident,reason,as_of))
        return ident
