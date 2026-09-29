"""REL004 conditional certification. NEVER treat a READY report as a certificate.

Each invocation re-evaluates source/evidence bytes. Three separate operator
principals approve the exact assessment. A fourth configured issuer seals it.
Diagnostic mode is the default and cannot emit production SUCCESS.
"""
from __future__ import annotations
import hashlib,hmac
from .contracts import SCHEMA,PublicationRequest,PublicationPolicy,shape
from .authority import AuthorityStore,approval_digest
from .evaluator import assess
from .journal import ReleaseJournal
from ..release_v2.contracts import ContractError,canonical_bytes,digest,integer,sha256

CERT_KEYS=('schema_version','release_id','release_version','environment_id','mode','status','candidate_digest','bundle_digest','request_digest',
    'publication_policy_digest','manifest_digest','graph_digest','assessment_digest','approval_digest','assessed_at','issued_at','expires_at','issuer_key_id','issuer_principal_id',
    'release_authorized','product_accepted','signature')

def _bytes(value):
    d=dict(value);d.pop('signature',None);return b'BIE-PRODUCTION-CERTIFICATE-1\x00'+canonical_bytes(d)

def issue(request:PublicationRequest,root,policy:PublicationPolicy,approvals,authorities:AuthorityStore,
          journal:ReleaseJournal,*,issuer_key_id:str,as_of:int,verifier=None,assessment_at:int|None=None):
    if type(authorities)is not AuthorityStore or type(journal)is not ReleaseJournal:raise ContractError('PUBLICATION_AUTHORITY_TYPE')
    integer(as_of,'as_of')
    assessment_at=as_of if assessment_at is None else assessment_at
    integer(assessment_at,'assessment_at',0,as_of)
    assessment=assess(request,root,policy,as_of=assessment_at,verifier=verifier)
    fresh=assessment if assessment_at==as_of else assess(request,root,policy,as_of=as_of,verifier=verifier)
    if not assessment.ready_for_signing or not fresh.ready_for_signing:raise ContractError('PUBLICATION_BLOCKED')
    end=authorities.check(approvals,assessment.content_digest,policy,as_of=as_of)
    key=authorities.key(issuer_key_id,'issuer',policy,as_of)
    if key.principal_id in {a.principal_id for a in approvals}:raise ContractError('ISSUER_NOT_INDEPENDENT')
    expires=min(end,as_of+policy.max_certificate_lifetime_seconds,assessment.manifest['evidence_expiry'],key.not_after)
    if expires<=as_of:raise ContractError('CERTIFICATE_NO_VALIDITY_WINDOW')
    production=policy.mode=='production'
    cert=dict(schema_version=SCHEMA,release_id=request.release_id,release_version=request.release_version,
        environment_id=policy.environment_id,mode=policy.mode,status='SUCCESS' if production else 'DIAGNOSTIC_ONLY',
        candidate_digest=request.bundle.candidate.content_digest,bundle_digest=request.bundle.content_digest,
        request_digest=request.content_digest,publication_policy_digest=policy.content_digest,
        manifest_digest=digest(assessment.manifest),graph_digest=digest(assessment.graph),assessment_digest=assessment.content_digest,
        approval_digest=approval_digest(approvals),assessed_at=assessment_at,issued_at=as_of,expires_at=expires,issuer_key_id=key.key_id,issuer_principal_id=key.principal_id,
        release_authorized=production,product_accepted=production,signature='')
    cert['signature']=hmac.new(key.secret,_bytes(cert),hashlib.sha256).hexdigest()
    journal.record(cert)
    return cert

def verify(certificate,request,root,policy,approvals,authorities,journal,*,as_of,verifier=None):
    shape(certificate,CERT_KEYS);c=certificate;integer(as_of,'as_of')
    integer(c['issued_at'],'issued_at');integer(c['assessed_at'],'assessed_at',0,c['issued_at']);integer(c['expires_at'],'expires_at',c['issued_at']+1)
    if not c['issued_at']<=as_of<c['expires_at']:raise ContractError('CERTIFICATE_TIME')
    if c['expires_at']-c['issued_at']>policy.max_certificate_lifetime_seconds:raise ContractError('CERTIFICATE_TTL')
    key=authorities.key(c['issuer_key_id'],'issuer',policy,as_of)
    if key.principal_id!=c['issuer_principal_id']:raise ContractError('CERTIFICATE_ISSUER')
    sha256(c['signature'],'signature')
    if not hmac.compare_digest(hmac.new(key.secret,_bytes(c),hashlib.sha256).hexdigest(),c['signature']):raise ContractError('CERTIFICATE_SIGNATURE')
    production=policy.mode=='production'
    if (c['schema_version'],c['release_id'],c['release_version'],c['environment_id'],c['mode'],c['status'])!=(SCHEMA,request.release_id,request.release_version,policy.environment_id,policy.mode,'SUCCESS' if production else 'DIAGNOSTIC_ONLY'):
        raise ContractError('CERTIFICATE_SCOPE')
    if c['release_authorized'] is not production or c['product_accepted'] is not production:raise ContractError('CERTIFICATE_PROMOTED')
    if (c['request_digest'],c['candidate_digest'],c['bundle_digest'],c['publication_policy_digest'])!=(request.content_digest,request.bundle.candidate.content_digest,request.bundle.content_digest,policy.content_digest):
        raise ContractError('CERTIFICATE_BINDING')
    fresh=assess(request,root,policy,as_of=as_of,verifier=verifier)
    if not fresh.ready_for_signing:raise ContractError('CERTIFICATE_CURRENT_EVIDENCE_BLOCKED')
    original=assess(request,root,policy,as_of=c['assessed_at'],verifier=verifier)
    if (c['assessment_digest'],c['manifest_digest'],c['graph_digest'])!=(original.content_digest,digest(original.manifest),digest(original.graph)):
        raise ContractError('CERTIFICATE_ASSESSMENT')
    end=authorities.check(approvals,original.content_digest,policy,as_of=as_of)
    if approval_digest(approvals)!=c['approval_digest']:raise ContractError('CERTIFICATE_APPROVAL_BINDING')
    if c['expires_at']>min(end,fresh.manifest['evidence_expiry'],key.not_after):raise ContractError('CERTIFICATE_EXCEEDS_EVIDENCE')
    if key.principal_id in {a.principal_id for a in approvals}:raise ContractError('ISSUER_NOT_INDEPENDENT')
    ident=journal.check(c)
    return dict(certificate_digest=ident,verified=True,status=c['status'],release_authorized=production,product_accepted=production)
