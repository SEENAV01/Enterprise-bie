"""HARD034 verified local content-addressed publication and atomic activation.

Every publish and read calls the actual existing certificate verifier. Blobs are
copied, not hard-linked from a mutable candidate. A SQLite transaction selects
one complete immutable capsule; partially prepared blobs are never an active
release. This is a private single-host store, not a distributed deployment/KMS.
"""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import os,sqlite3,tempfile,stat,json
from .common import *
from ..publication_v2.certification import verify as verify_certificate
from ..publication_v2.evaluator import assess


def _sync_dir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)

class PublicationStore:
    def __init__(self,path,*,create=False):
        self.path=Path(path).absolute()
        if create:self.path.mkdir(mode=0o700,parents=True,exist_ok=False)
        real_dir(self.path)
        require(self.path.stat().st_uid==os.getuid() and not self.path.stat().st_mode&0o077,'H7_STORE_PRIVATE')
        self.blobs=self.path/'blobs';self.db=self.path/'publication.sqlite3'
        if create:
            self.blobs.mkdir(mode=0o700)
            with self._tx() as c:
                c.execute('CREATE TABLE metadata(version INTEGER NOT NULL)');c.execute('INSERT INTO metadata VALUES(1)')
                c.execute('CREATE TABLE releases(release_id TEXT,version TEXT,capsule_sha TEXT NOT NULL,capsule TEXT NOT NULL,PRIMARY KEY(release_id,version))')
                c.execute('CREATE TABLE active(release_id TEXT PRIMARY KEY,version TEXT NOT NULL,capsule_sha TEXT NOT NULL)')
                c.execute('CREATE TABLE audit(n INTEGER PRIMARY KEY,body TEXT NOT NULL,previous TEXT NOT NULL,hash TEXT NOT NULL)')
            _sync_dir(self.path)
        else:
            require(self.db.is_file() and self.blobs.is_dir(),'H7_STORE_NOT_INITIALIZED')
            with self._tx() as c:require(c.execute('SELECT version FROM metadata').fetchall()==[(1,)],'H7_STORE_SCHEMA');self._audit_verify(c)
    @contextmanager
    def _tx(self):
        for p in (self.db,self.blobs):require(not p.is_symlink(),'H7_STORE_LINK')
        if self.db.exists():require(self.db.stat().st_nlink==1 and stat.S_ISREG(self.db.stat().st_mode),'H7_STORE_DATABASE_UNSAFE')
        c=sqlite3.connect(self.db,timeout=15,isolation_level=None)
        try:
            c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA synchronous=FULL');c.execute('BEGIN IMMEDIATE')
            yield c;c.execute('COMMIT')
        except BaseException:
            if c.in_transaction:c.execute('ROLLBACK')
            raise
        finally:c.close()
    def _audit_verify(self,c):
        prev='0'*64;num=0
        for n,body,p,h in c.execute('SELECT n,body,previous,hash FROM audit ORDER BY n'):
            require(n==num+1 and p==prev and h==digest(dict(n=n,body=strict_object(body.encode()),previous=p)),'H7_STORE_AUDIT_CORRUPT');prev=h;num=n
        return num,prev
    def _event(self,c,body):
        n,prev=self._audit_verify(c);n+=1;h=digest(dict(n=n,body=body,previous=prev))
        c.execute('INSERT INTO audit VALUES(?,?,?,?)',(n,canonical_bytes(body).decode(),prev,h))
    def put(self,data):
        require(type(data) is bytes and len(data)<=64*1024*1024,'H7_BLOB_LIMIT')
        h=identity(data);target=self.blobs/h
        if target.exists():require(regular_bytes(self.blobs,h)==data,'H7_BLOB_CORRUPTION');return h
        fd,tmp=tempfile.mkstemp(prefix='.prepare-',dir=self.blobs)
        try:
            with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
            os.chmod(tmp,0o400)
            try:os.link(tmp,target,follow_symlinks=False)
            except FileExistsError:pass
        finally:os.unlink(tmp)
        _sync_dir(self.blobs)
        require(regular_bytes(self.blobs,h)==data,'H7_BLOB_CORRUPTION');return h
    def _get(self,h):
        sha256(h,'blob');data=regular_bytes(self.blobs,h);require(identity(data)==h,'H7_BLOB_CORRUPTION');return data
    @contextmanager
    def _restore(self,refs):
        with tempfile.TemporaryDirectory(prefix='bie-h7-verify-') as d:
            root=Path(d)
            for r in refs:
                ref=ArtifactRef(**r);data=self._get(ref.sha256)
                require(len(data)==ref.size,'H7_BLOB_SIZE')
                p=root/ref.path;p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as f:f.write(data)
            yield root
    @staticmethod
    def _current_time(policy, fixed, now, authorization_guard):
        """Trusted in-process guard, never loaded from candidate JSON.

        Production calls require renewed authority at each boundary. Historical
        diagnostic callers may use a fixed clock; they cannot authorize release.
        """
        integer(now, 'now')
        require(authorization_guard is None or callable(authorization_guard),
                'H39_PUBLICATION_GUARD_TYPE')
        require(policy.mode != 'production' or authorization_guard is not None,
                'H39_PUBLICATION_FRESH_AUTHORITY_REQUIRED')
        value = now if authorization_guard is None else authorization_guard(fixed)
        integer(value, 'authorization_time')
        require(value >= now, 'H39_AUTHORIZATION_CLOCK_ROLLBACK')
        return value

    def publish(self,request,source,policy,approvals,authorities,journal,certificate,*,
                now,verifier=None,expected_head=None,authorization_guard=None):
        last_time = now
        def recheck(fixed):
            nonlocal last_time
            last_time = self._current_time(policy, fixed, last_time, authorization_guard)
            verify_certificate(certificate,request,fixed,policy,approvals,authorities,
                               journal,as_of=last_time,verifier=verifier)
            return last_time
        recheck(source)
        assessment=assess(request,source,policy,as_of=certificate['assessed_at'],verifier=verifier)
        require(assessment.ready_for_signing,'H7_PUBLICATION_BLOCKED')
        refs=assessment.manifest['artifacts']
        require(len({r['path'] for r in refs})==len(refs),'H7_CAPSULE_PATH_ALIAS')
        from ..source_v2.io import SnapshotStore
        with SnapshotStore(source) as snapshot:
            for r in refs:
                ref=ArtifactRef(**r)
                require(self.put(snapshot.read(ref))==ref.sha256,'H7_SNAPSHOT_CHANGED')
        capsule=dict(schema_version='bie.qa.immutable-capsule/1',release_id=request.release_id,
            version=request.release_version,request_digest=request.content_digest,
            policy_digest=policy.content_digest,certificate=certificate,artifacts=refs)
        capsule_sha=digest(capsule)
        # Keep the inspected copy alive through the activation transaction. A
        # failed final authority check rolls back active/releases/audit together.
        with self._restore(refs) as fixed:
            recheck(fixed)
            with self._tx() as c:
                self._audit_verify(c)
                recheck(fixed)  # Includes time spent waiting for the write lock.
                old=c.execute('SELECT capsule_sha FROM active WHERE release_id=?',
                              (request.release_id,)).fetchone()
                current=old[0] if old else None
                existing=c.execute('SELECT capsule_sha FROM releases WHERE release_id=? AND version=?',
                    (request.release_id,request.release_version)).fetchone()
                if existing:
                    require(existing[0]==capsule_sha,'H7_IMMUTABLE_VERSION_CONFLICT')
                    if current==capsule_sha:
                        recheck(fixed)
                        return dict(status='ALREADY_PUBLISHED',capsule_sha256=capsule_sha,
                                    production_authorized=certificate['release_authorized'])
                require(current==expected_head,'H7_ACTIVATION_CONFLICT')
                if not existing:
                    c.execute('INSERT INTO releases VALUES(?,?,?,?)',
                        (request.release_id,request.release_version,capsule_sha,canonical_bytes(capsule).decode()))
                c.execute('INSERT INTO active VALUES(?,?,?) ON CONFLICT(release_id) DO UPDATE SET version=excluded.version,capsule_sha=excluded.capsule_sha',
                          (request.release_id,request.release_version,capsule_sha))
                self._event(c,dict(kind='ACTIVATE',release_id=request.release_id,
                    version=request.release_version,capsule_sha256=capsule_sha,previous=current,at=last_time))
                recheck(fixed)  # Last authorization check before transaction commit.
        return dict(status='LOCAL_PUBLISHED',capsule_sha256=capsule_sha,
            production_authorized=certificate['release_authorized'],product_accepted=certificate['product_accepted'])

    def serve(self,release_id,artifact_id,request,policy,approvals,authorities,journal,*,
              now,verifier=None,authorization_guard=None):
        token(release_id,'release_id');token(artifact_id,'artifact_id')
        with self._tx() as c:
            self._audit_verify(c)
            row=c.execute('SELECT r.capsule_sha,r.capsule FROM releases r JOIN active a ON a.release_id=r.release_id AND a.version=r.version WHERE r.release_id=? AND a.capsule_sha=r.capsule_sha',
                          (release_id,)).fetchone()
            require(row is not None,'H7_RELEASE_NOT_ACTIVE')
            capsule=strict_object(row[1].encode())
            require(digest(capsule)==row[0],'H7_CAPSULE_CORRUPTION')
            require(capsule['request_digest']==request.content_digest and
                    capsule['policy_digest']==policy.content_digest,'H7_SERVING_CONTEXT_CHANGED')
            with self._restore(capsule['artifacts']) as fixed:
                current = self._current_time(policy, fixed, now, authorization_guard)
                verify_certificate(capsule['certificate'],request,fixed,policy,approvals,
                                   authorities,journal,as_of=current,verifier=verifier)
                matches=[ArtifactRef(**r) for r in capsule['artifacts'] if r['artifact_id']==artifact_id]
                require(len(matches)==1,'H7_ARTIFACT_NOT_IN_RELEASE')
                value=regular_bytes(fixed,matches[0].path)
                current = self._current_time(policy, fixed, current, authorization_guard)
                verify_certificate(capsule['certificate'],request,fixed,policy,approvals,
                                   authorities,journal,as_of=current,verifier=verifier)
            return value  # Never return a mutable filesystem path as verified bytes.
    def deactivate(self,release_id,*,expected_head,reason,now):
        token(release_id,'release_id');sha256(expected_head,'head');text(reason,'reason',512);integer(now,'now')
        with self._tx() as c:
            self._audit_verify(c);r=c.execute('SELECT capsule_sha FROM active WHERE release_id=?',(release_id,)).fetchone()
            require(r is not None and r[0]==expected_head,'H7_ACTIVATION_CONFLICT')
            c.execute('DELETE FROM active WHERE release_id=?',(release_id,));self._event(c,dict(kind='DEACTIVATE',release_id=release_id,capsule_sha256=expected_head,reason=reason,at=now))
        return {'status':'LOCAL_DEACTIVATED','distributed_revocation':False}
