"""HARD035: public-key attestations, nonce-bound time and revocation snapshots.

Uses cryptography's Ed25519 verification, never user-supplied executable callbacks.
Keys are provisioned out of band. Time/status responses must be supplied by a
separately operated service. This module neither deploys that service nor claims
NTS/RFC3161/TPM attestation. A signature authenticates a statement, not its truth.
Persistent watermarks resist stale messages, not an administrator restoring the DB.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from contextlib import contextmanager
import os,sqlite3,secrets,time,threading,stat
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from .common import *

DOMAIN=b'BIE-QA-ASSURANCE-V1\x00'
PURPOSES=('clock','status','capture','review','issuer','rights','memory','eval')

def signing_bytes(envelope):
    """Public canonical encoding; intentionally no signer/private-key implementation."""
    fields(envelope,('schema_version','key_id','purpose','subject_digest','binding',
        'nonce','created_at','expires_at','payload','signature'),'H8_ENVELOPE_FIELDS')
    require(envelope['schema_version']=='bie.qa.signed-assurance/1','H8_ENVELOPE_SCHEMA')
    token(envelope['key_id'],'key');require(envelope['purpose'] in PURPOSES,'H8_PURPOSE')
    sha256(envelope['subject_digest'],'subject');sha256(envelope['nonce'],'nonce')
    Binding(**fields(envelope['binding'],('run_id','revision','candidate_digest','policy_digest'),'H8_BINDING_FIELDS'))
    integer(envelope['created_at'],'created');integer(envelope['expires_at'],'expires',envelope['created_at']+1)
    require(type(envelope['payload']) is dict,'H8_PAYLOAD')
    require(type(envelope['signature']) is str and len(envelope['signature'])==128 and
        all(c in '0123456789abcdef' for c in envelope['signature']),'H8_SIGNATURE_ENCODING')
    raw=DOMAIN+canonical_bytes({k:v for k,v in envelope.items() if k!='signature'})
    require(len(raw)<=2*1024*1024,'H8_ENVELOPE_LIMIT')
    return raw

@dataclass(frozen=True)
class PublicAuthority:
    key_id:str
    principal_id:str
    independence_group:str
    public_key_hex:str
    purposes:tuple[str,...]
    not_before:int
    not_after:int
    assurance:str='DIAGNOSTIC'
    def __post_init__(self):
        for k in ('key_id','principal_id','independence_group'):token(getattr(self,k),k)
        sha256(self.public_key_hex,'ed25519.public')
        exact_strings(self.purposes,'H8_KEY_PURPOSES',1,len(PURPOSES))
        require(set(self.purposes)<=set(PURPOSES),'H8_KEY_PURPOSES')
        integer(self.not_before,'not_before');integer(self.not_after,'not_after',self.not_before+1)
        require(self.assurance in ('DIAGNOSTIC','OPERATOR_PROVISIONED'),'H8_KEY_ASSURANCE')

@dataclass(frozen=True)
class TrustPolicy:
    policy_id:str
    tenant_id:str
    keys:tuple[PublicAuthority,...]
    mode:str='diagnostic'
    clock_quorum:int=2
    minimum_status_epoch:int=1
    max_clock_roundtrip_ms:int=10000
    max_clock_uncertainty_ms:int=2000
    session_ttl_ms:int=30000
    max_statement_age_seconds:int=86400
    def __post_init__(self):
        token(self.policy_id,'trust.policy');token(self.tenant_id,'tenant')
        require(type(self.keys) is tuple and 1<=len(self.keys)<=256 and
            all(type(k) is PublicAuthority for k in self.keys),'H8_KEYS')
        require(len({k.key_id for k in self.keys})==len(self.keys),'H8_KEY_ALIAS')
        # A shared public key cannot be multiplied into distinct approval identities.
        require(len({k.public_key_hex for k in self.keys})==len(self.keys),'H8_SHARED_PUBLIC_KEY')
        require(self.mode in ('diagnostic','production'),'H8_TRUST_MODE')
        integer(self.clock_quorum,'quorum',1,8)
        if self.mode=='production':require(self.clock_quorum>=2,'H8_PRODUCTION_CLOCK_QUORUM')
        integer(self.minimum_status_epoch,'epoch',1)
        integer(self.max_clock_roundtrip_ms,'rtt',1,60000)
        integer(self.max_clock_uncertainty_ms,'uncertainty',0,10000)
        integer(self.session_ttl_ms,'ttl',1,300000)
        integer(self.max_statement_age_seconds,'age',1,31536000)
    @property
    def content_digest(self):return digest(asdict(self))

class AuthorityJournal:
    """Private durable anti-replay watermarks; intentionally not a remote KMS."""
    def __init__(self,path,*,create=False):
        self.path=Path(path).absolute()
        if create:self.path.mkdir(mode=0o700,parents=True,exist_ok=False)
        real_dir(self.path)
        require(self.path.stat().st_uid==os.getuid() and not self.path.stat().st_mode&0o077,'H8_JOURNAL_PRIVATE')
        self.db=self.path/'authority.sqlite3'
        if create:
            with self.transaction() as c:
                c.execute('CREATE TABLE meta(version INTEGER)');c.execute('INSERT INTO meta VALUES(1)')
                c.execute('CREATE TABLE watermarks(tenant TEXT PRIMARY KEY,epoch INTEGER,time_lower_ms INTEGER,status_sha TEXT)')
                c.execute('CREATE TABLE nonces(tenant TEXT,nonce TEXT,PRIMARY KEY(tenant,nonce))')
        else:
            require(self.db.is_file(),'H8_JOURNAL_MISSING')
            with self.transaction() as c:require(c.execute('SELECT version FROM meta').fetchall()==[(1,)],'H8_JOURNAL_SCHEMA')
    @contextmanager
    def transaction(self):
        for p in (self.db,Path(str(self.db)+'-wal'),Path(str(self.db)+'-shm')):
            if p.exists() or p.is_symlink():
                require(not p.is_symlink() and p.is_file() and p.stat().st_nlink==1,'H8_JOURNAL_LINK')
        c=sqlite3.connect(self.db,timeout=10,isolation_level=None)
        try:
            c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA synchronous=FULL');c.execute('BEGIN IMMEDIATE')
            yield c;c.execute('COMMIT')
        except BaseException:
            if c.in_transaction:c.execute('ROLLBACK')
            raise
        finally:c.close()
    def accept(self,tenant,nonce,epoch,lower,status_sha):
        with self.transaction() as c:
            old=c.execute('SELECT epoch,time_lower_ms,status_sha FROM watermarks WHERE tenant=?',(tenant,)).fetchone()
            if old:
                require(epoch>=old[0],'H8_STATUS_ROLLBACK')
                require(lower>=old[1],'H8_CLOCK_ROLLBACK')
                require(epoch!=old[0] or status_sha==old[2],'H8_STATUS_EQUIVOCATION')
            require(c.execute('SELECT 1 FROM nonces WHERE tenant=? AND nonce=?',(tenant,nonce)).fetchone() is None,'H8_REPLAY')
            c.execute('INSERT INTO nonces VALUES(?,?)',(tenant,nonce))
            c.execute('INSERT INTO watermarks VALUES(?,?,?,?) ON CONFLICT(tenant) DO UPDATE SET epoch=excluded.epoch,time_lower_ms=excluded.time_lower_ms,status_sha=excluded.status_sha',
                (tenant,epoch,lower,status_sha))

class AuthoritySession:
    """One short-lived, nonce-bound verification context. No caller-supplied UTC clock.

    Policy, binding and journal are operator inputs. The monotonic clock is an
    explicit trusted injection seam for deterministic tests, never parsed from JSON.
    Refresh by starting a new session with fresh signed time and status responses.
    """
    def __init__(self,policy,binding,journal,*,monotonic_ns=time.monotonic_ns):
        require(type(policy) is TrustPolicy and type(binding) is Binding and type(journal) is AuthorityJournal,'H8_SESSION_CONFIG')
        self.policy=policy;self.binding=binding;self.journal=journal;self._clock=monotonic_ns
        self._nonce=secrets.token_hex(32);self._started=self._clock();self._ready=False;self._lock=threading.RLock()
        self._keys={k.key_id:k for k in policy.keys}
    @property
    def challenge(self):
        return {'schema_version':'bie.qa.authority-challenge/1','nonce':self._nonce,
            'tenant_id':self.policy.tenant_id,'trust_digest':self.policy.content_digest,'binding':asdict(self.binding)}
    @property
    def challenge_digest(self):return digest(self.challenge)
    def _signature(self,e,purpose,subject):
        raw=signing_bytes(e)
        require(e['purpose']==purpose and e['subject_digest']==subject,'H8_STATEMENT_SCOPE')
        require(e['binding']==asdict(self.binding) and e['nonce']==self._nonce,'H8_STATEMENT_BINDING')
        key=self._keys.get(e['key_id']);require(key is not None,'H8_UNKNOWN_KEY')
        require(purpose in key.purposes,'H8_KEY_PURPOSE')
        if self.policy.mode=='production':require(key.assurance=='OPERATOR_PROVISIONED','H8_DIAGNOSTIC_AUTHORITY')
        try:Ed25519PublicKey.from_public_bytes(bytes.fromhex(key.public_key_hex)).verify(bytes.fromhex(e['signature']),raw)
        except (InvalidSignature,ValueError) as exc:raise ContractError('H8_BAD_SIGNATURE') from exc
        return key
    @staticmethod
    def _lifetime(e,key,lo,hi):
        require(e['created_at']*1000<=lo and hi<e['expires_at']*1000,'H8_STATEMENT_TIME')
        require(key.not_before*1000<=lo and hi<key.not_after*1000,'H8_AUTHORITY_TIME')
    def establish(self,time_responses,status_response):
        with self._lock:
            require(not self._ready,'H8_SESSION_ALREADY_ESTABLISHED')
            end=self._clock();rtt=(end-self._started+999999)//1000000
            require(0<=rtt<=self.policy.max_clock_roundtrip_ms,'H8_CLOCK_ROUNDTRIP')
            require(type(time_responses) is tuple and len(time_responses)==self.policy.clock_quorum,'H8_CLOCK_QUORUM')
            keys=[];windows=[]
            for e in time_responses:
                k=self._signature(e,'clock',self.challenge_digest)
                p=fields(e['payload'],('utc_ms','uncertainty_ms','trust_digest'),'H8_CLOCK_PAYLOAD')
                integer(p['utc_ms'],'utc');integer(p['uncertainty_ms'],'uncertainty',0,self.policy.max_clock_uncertainty_ms)
                require(p['trust_digest']==self.policy.content_digest,'H8_TRUST_BINDING')
                windows.append((p['utc_ms']-p['uncertainty_ms'],p['utc_ms']+p['uncertainty_ms']+rtt));keys.append(k)
            require(len({k.principal_id for k in keys})==len(keys) and len({k.independence_group for k in keys})==len(keys),'H8_CLOCK_INDEPENDENCE')
            lo=max(x[0] for x in windows);hi=min(x[1] for x in windows)
            require(0<=lo<=hi,'H8_CLOCK_DISAGREEMENT')
            for e,k in zip(time_responses,keys):self._lifetime(e,k,lo,hi)
            sk=self._signature(status_response,'status',self.policy.content_digest)
            require(sk.principal_id not in {k.principal_id for k in keys} and
                    sk.independence_group not in {k.independence_group for k in keys},
                    'H39_CLOCK_STATUS_INDEPENDENCE')
            self._lifetime(status_response,sk,lo,hi)
            p=fields(status_response['payload'],('epoch','revoked_key_ids','trust_digest'),'H8_STATUS_PAYLOAD')
            integer(p['epoch'],'epoch',self.policy.minimum_status_epoch)
            exact_strings(p['revoked_key_ids'],'H8_REVOKED_IDS')
            require(set(p['revoked_key_ids'])<=set(self._keys),'H8_UNKNOWN_REVOCATION')
            require(p['trust_digest']==self.policy.content_digest,'H8_TRUST_BINDING')
            require(not set(k.key_id for k in keys+[sk])&set(p['revoked_key_ids']),'H8_ROOT_REVOKED')
            require(lo-status_response['created_at']*1000<=self.policy.max_statement_age_seconds*1000,'H8_STATUS_STALE')
            # Nonce-specific signatures differ; compare epoch payload for equivocation.
            self.journal.accept(self.policy.tenant_id,self._nonce,p['epoch'],lo,digest(p))
            self._lower=lo;self._upper=hi;self._received=end;self._status_expiry=status_response['expires_at']*1000
            self._authority_expiry=min([status_response['expires_at']*1000,sk.not_after*1000]+[min(e['expires_at'],k.not_after)*1000 for e,k in zip(time_responses,keys)])
            self._revoked=frozenset(p['revoked_key_ids']);self._ready=True
            self._roots=frozenset(k.principal_id for k in keys+[sk])
            self._root_groups=frozenset(k.independence_group for k in keys+[sk])
            return {'verified':True,'utc_interval_ms':[lo,hi],'status_epoch':p['epoch'],
                'mode':self.policy.mode,'operational_service_provisioned':False}
    def window(self):
        require(self._ready,'H8_TIME_NOT_ESTABLISHED')
        elapsed=(self._clock()-self._received)//1000000
        require(0<=elapsed<=self.policy.session_ttl_ms,'H8_SESSION_EXPIRED')
        lo=self._lower+elapsed;hi=self._upper+elapsed
        require(hi<self._status_expiry,'H8_STATUS_EXPIRED')
        require(hi<self._authority_expiry,'H8_ROOT_TIME_EXPIRED')
        return lo,hi
    def verify(self,envelope,*,purpose,subject_digest,expected_payload=None):
        with self._lock:
            lo,hi=self.window();key=self._signature(envelope,purpose,subject_digest)
            require(key.key_id not in self._revoked,'H8_KEY_REVOKED')
            if purpose not in ('clock','status'):
                require(key.principal_id not in self._roots,'H8_ROOT_SIGNED_CONTENT')
                require(key.independence_group not in self._root_groups,'H39_ROOT_GROUP_CONTENT')

            self._lifetime(envelope,key,lo,hi)
            require(lo-envelope['created_at']*1000<=self.policy.max_statement_age_seconds*1000,'H8_STATEMENT_STALE')
            if expected_payload is not None:require(envelope['payload']==expected_payload,'H8_PAYLOAD_BINDING')
            return {'key_id':key.key_id,'principal_id':key.principal_id,'independence_group':key.independence_group,
                'envelope_sha256':digest(envelope),'diagnostic':key.assurance=='DIAGNOSTIC'}
    def verify_roles(self,envelopes,subject_digest,required=('capture','review','issuer')):
        exact_strings(required,'H39_REQUIRED_ROLES',1,len(PURPOSES)-2)
        require(set(required)<=set(PURPOSES)-{'clock','status'},'H39_REQUIRED_ROLES')
        require(type(envelopes) is tuple and len(envelopes)==len(required),'H8_ROLE_CENSUS')
        require(all(type(e) is dict and 'purpose' in e for e in envelopes),'H8_ROLE_FIELDS')
        require({e['purpose'] for e in envelopes}==set(required),'H8_ROLE_CENSUS')
        verified=[self.verify(e,purpose=e['purpose'],subject_digest=subject_digest,
            expected_payload={'decision':'APPROVE','trust_digest':self.policy.content_digest}) for e in envelopes]
        require(len({r['principal_id'] for r in verified})==len(verified) and
            len({r['independence_group'] for r in verified})==len(verified),'H8_ROLE_INDEPENDENCE')
        require(not self._roots & {r['principal_id'] for r in verified},'H8_ROOT_SIGNED_CONTENT')
        return verified

class AttestedPublication:
    """Additional public assurance around H7's actual immutable publication store.

    Existing certificate, 28-gate, inventory and HMAC checks still execute. No
    conversion of an external signature into an inherited production certificate.
    Raw H7 callers must be migrated by the operator before this is a mandatory gate.
    """
    def __init__(self,store):
        from ..operational_quality_v2.publication import PublicationStore
        require(type(store) is PublicationStore,'H8_PUBLICATION_STORE');self.store=store
    def publish(self,request,source,policy,approvals,authorities,journal,certificate,*,session,envelopes,verifier=None,expected_head=None):
        require(type(session) is AuthoritySession,'H8_SESSION_REQUIRED')
        require(session.binding.candidate_digest==request.bundle.candidate.content_digest and session.binding.run_id==request.bundle.candidate.run_id and
            session.binding.revision==request.bundle.candidate.revision and session.binding.policy_digest==policy.content_digest,'H8_PUBLICATION_BINDING')
        require(policy.mode==session.policy.mode,'H8_MODE_MISMATCH')
        subject=digest({'request_digest':request.content_digest,'certificate_digest':digest(certificate),'operation':'publish'})
        session.verify_roles(envelopes,subject)
        lo,hi=session.window()
        # Check legacy not-before against the lower clock bound as well as expiry at the upper.
        from ..publication_v2.certification import verify as verify_certificate
        verify_certificate(certificate,request,source,policy,approvals,authorities,journal,as_of=lo//1000,verifier=verifier)
        def guard(fixed):
            session.verify_roles(envelopes,subject)
            lower,upper=session.window()
            verify_certificate(certificate,request,fixed,policy,approvals,authorities,
                               journal,as_of=lower//1000,verifier=verifier)
            return (upper+999)//1000
        result=self.store.publish(request,source,policy,approvals,authorities,journal,certificate,
            now=(hi+999)//1000,verifier=verifier,expected_head=expected_head,authorization_guard=guard)
        result['public_assurance_digest']=subject
        return result
    def serve(self,release_id,artifact_id,request,policy,approvals,authorities,journal,*,session,envelopes,verifier=None):
        require(type(session) is AuthoritySession and policy.mode==session.policy.mode,'H8_SESSION_REQUIRED')
        require(session.binding.candidate_digest==request.bundle.candidate.content_digest and session.binding.run_id==request.bundle.candidate.run_id and
            session.binding.revision==request.bundle.candidate.revision and session.binding.policy_digest==policy.content_digest,'H8_PUBLICATION_BINDING')
        subject=digest({'request_digest':request.content_digest,'release_id':release_id,'artifact_id':artifact_id,'operation':'serve'})
        session.verify_roles(envelopes,subject)
        lo,hi=session.window()
        def guard(fixed):
            session.verify_roles(envelopes,subject)
            _,upper=session.window()
            return (upper+999)//1000
        return self.store.serve(release_id,artifact_id,request,policy,approvals,authorities,journal,
            now=(hi+999)//1000,verifier=verifier,authorization_guard=guard)
