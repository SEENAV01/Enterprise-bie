"""H5-003 executor signatures over exact request, kernel proof and artifact bytes.

Keys remain host-side. This authorizes an executor assertion, not pronunciation,
cinematic quality, upstream authorship, whole-host security or product acceptance.
"""
from __future__ import annotations
import re
import math
import time
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey,Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from .common import AudioError, digest, integer, text
from .acoustic_contract import canonical, fields, plain
from .pipeline_contract import OPERATION,SCOPE,BOUNDARIES,validate_request
from .pipeline_profile import validate_profile
from .pipeline_runtime import run_local_pipeline,validate_execution

DOMAIN=b'BIE-AUDIO-LOCAL-PIPELINE-EXECUTOR-V1\0'
SCHEMA='bie.audio.signed-pipeline-execution/1'


def validate_trust(trust):
    fields(trust,('schema_version','revision','scope','max_age_seconds','max_future_skew_seconds','issuers'))
    if trust['schema_version']!='bie.audio.pipeline-trust/1' or trust['scope']!=SCOPE:
        raise AudioError('PIPELINE_TRUST_SCHEMA')
    text(trust['revision'],'trust revision',256)
    integer(trust['max_age_seconds'],'max age',1,604800)
    integer(trust['max_future_skew_seconds'],'clock skew',0,300)
    if type(trust['issuers'])is not list or not 1<=len(trust['issuers'])<=100:
        raise AudioError('PIPELINE_TRUST_ISSUERS')
    seen=set()
    for row in trust['issuers']:
        fields(row,('key_id','role','public_key_hex','profile_fingerprints','not_before','not_after','revoked'))
        text(row['key_id'],'key',256)
        if row['key_id'] in seen:raise AudioError('PIPELINE_DUPLICATE_ISSUER')
        seen.add(row['key_id'])
        if row['role']!='audio-pipeline-executor' or type(row['revoked'])is not bool:
            raise AudioError('PIPELINE_ISSUER_ROLE')
        if type(row['public_key_hex'])is not str or not re.fullmatch('[0-9a-f]{64}',row['public_key_hex']):
            raise AudioError('PIPELINE_PUBLIC_KEY')
        for k in ('not_before','not_after'):integer(row[k],k,0,2**53)
        if row['not_after']<=row['not_before']:raise AudioError('PIPELINE_ISSUER_TIME')
        profiles=row['profile_fingerprints']
        if type(profiles)is not list or not 1<=len(profiles)<=100 or len(set(profiles))!=len(profiles):
            raise AudioError('PIPELINE_PROFILE_APPROVALS')
        for p in profiles:digest(p)
    return trust


def authorize(profile,trust,key_id,*,signer=None,now=None):
    validate_trust(trust)
    current=time.time() if now is None else now
    # Lease APIs use finite fractional wall clocks; receipt fields remain integer seconds.
    if type(current) not in (int,float) or not math.isfinite(current) or not 0<=current<=2**53:
        raise AudioError('PIPELINE_VERIFICATION_TIME')
    issuer=next((x for x in trust['issuers'] if x['key_id']==key_id),None)
    if (issuer is None or issuer['revoked'] or profile['fingerprint'] not in issuer['profile_fingerprints']
        or not issuer['not_before']<=current<issuer['not_after']):
        raise AudioError('PIPELINE_EXECUTOR_NOT_AUTHORIZED')
    if signer is not None:
        if not isinstance(signer,Ed25519PrivateKey):raise AudioError('PIPELINE_SIGNER_TYPE')
        public=signer.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()
        if public!=issuer['public_key_hex']:raise AudioError('PIPELINE_SIGNER_MISMATCH')
    return issuer,current


def issue_execution(request,profile,trust,signer,*,cancellation=None,lock_root=None):
    request,profile,trust=map(plain,(request,profile,trust))
    if signer is None:raise AudioError('PIPELINE_SIGNER_REQUIRED')
    validate_request(request);validate_profile(profile)
    authorize(profile,trust,request['key_id'],signer=signer)
    files,execution=run_local_pipeline(request,profile,cancellation=cancellation,lock_root=lock_root)
    if cancellation is not None and cancellation.is_set():raise AudioError('PIPELINE_CANCELLED')
    issuer,current=authorize(profile,trust,request['key_id'],signer=signer)
    issued=int(current)
    payload={'schema_version':'bie.audio.pipeline-executor-payload/1','operation':OPERATION,'scope':SCOPE,
        'key_id':request['key_id'],'issued_at':issued,
        'expires_at':min(issued+trust['max_age_seconds'],issuer['not_after']),
        'request_fingerprint':request['fingerprint'],'profile_fingerprint':profile['fingerprint'],
        'execution':execution,**BOUNDARIES}
    receipt={'schema_version':SCHEMA,'payload':payload,
        'signature_ed25519_hex':signer.sign(DOMAIN+canonical(payload)).hex()}
    verify_receipt(receipt,files,request,profile,trust)
    return files,receipt


def verify_receipt(receipt,files,request,profile,trust,*,now=None):
    validate_request(request);validate_profile(profile)
    if request['profile_fingerprint']!=profile['fingerprint']:raise AudioError('PIPELINE_PROFILE_BINDING')
    fields(receipt,('schema_version','payload','signature_ed25519_hex'))
    if receipt['schema_version']!=SCHEMA:raise AudioError('PIPELINE_RECEIPT_SCHEMA')
    p=receipt['payload']
    fields(p,('schema_version','operation','scope','key_id','issued_at','expires_at',
        'request_fingerprint','profile_fingerprint','execution',*BOUNDARIES))
    if (p['schema_version']!='bie.audio.pipeline-executor-payload/1' or p['operation']!=OPERATION
        or p['scope']!=SCOPE or p['key_id']!=request['key_id']
        or p['request_fingerprint']!=request['fingerprint'] or p['profile_fingerprint']!=profile['fingerprint']
        or any(p[k] is not v for k,v in BOUNDARIES.items())):
        raise AudioError('PIPELINE_RECEIPT_BINDING')
    issuer,current=authorize(profile,trust,p['key_id'],now=now)
    for k in ('issued_at','expires_at'):integer(p[k],k,0,2**53)
    if (p['issued_at']>current+trust['max_future_skew_seconds'] or p['expires_at']<=current
        or p['expires_at']<=p['issued_at'] or current-p['issued_at']>trust['max_age_seconds']
        or p['expires_at']-p['issued_at']>trust['max_age_seconds']
        or not issuer['not_before']<=p['issued_at']<issuer['not_after'] or p['expires_at']>issuer['not_after']):
        raise AudioError('PIPELINE_RECEIPT_EXPIRED_OR_FUTURE')
    sig=receipt['signature_ed25519_hex']
    if type(sig)is not str or not re.fullmatch('[0-9a-f]{128}',sig):raise AudioError('PIPELINE_SIGNATURE_FORMAT')
    try:Ed25519PublicKey.from_public_bytes(bytes.fromhex(issuer['public_key_hex'])).verify(bytes.fromhex(sig),DOMAIN+canonical(p))
    except (ValueError,InvalidSignature) as exc:raise AudioError('PIPELINE_SIGNATURE_INVALID') from exc
    validate_execution(p['execution'],files,request,profile)
    return {'signature_reverified':True,'request_fingerprint':request['fingerprint'],
        'files':p['execution']['files'],'scope':SCOPE,**BOUNDARIES}
