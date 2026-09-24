"""H4-R1-003: externally approved profiles and signed v2 execution provenance.

The embedded v1 receipt serves existing QA only; it alone never proves isolation.
An issuer signature authenticates its assertion, not a compromised host or model.
"""
from __future__ import annotations
import hashlib
import re
import time
from .common import AudioError, digest, integer, text
from .acoustic_contract import BOUNDARIES, SCOPE, canonical, fields, plain, validate_job
from .acoustic_evidence import validate_trust, verify_receipt, validate_measurement
from .durable_pipeline import authorize_signer
from .kernel_profile import KERNEL_SCOPE, validate_profile
from .kernel_runtime import run_kernel, validate_execution

DOMAIN = b'BIE-AUDIO-KERNEL-EVALUATOR-V2\0'
SCHEMA = 'bie.audio.signed-kernel-evaluation/2'


def validate_kernel_trust(trust):
    fields(trust, ('schema_version','revision','scope','evaluator_trust','profile_fingerprints'),
           'KERNEL_TRUST_FIELDS')
    if trust['schema_version'] != 'bie.audio.kernel-trust/1' or trust['scope'] != KERNEL_SCOPE:
        raise AudioError('KERNEL_TRUST_SCHEMA')
    text(trust['revision'], 'kernel trust revision', 256)
    validate_trust(trust['evaluator_trust'])
    profiles = trust['profile_fingerprints']
    if type(profiles) is not list or not 1 <= len(profiles) <= 100:
        raise AudioError('KERNEL_TRUST_PROFILE_ALLOWLIST')
    for profile in profiles:
        digest(profile)
    if len(set(profiles)) != len(profiles):
        raise AudioError('KERNEL_TRUST_DUPLICATE_PROFILE')
    return trust


def _approved(profile, runtime, trust):
    validate_kernel_trust(trust)
    validate_profile(profile, runtime)
    if profile['fingerprint'] not in trust['profile_fingerprints']:
        raise AudioError('KERNEL_PROFILE_NOT_APPROVED')


def issue_kernel_evaluation(job, wav, runtime, profile, trust, signer, key_id,
                            *, cancellation=None, lock_root=None, now=None, request_fingerprint=None):
    job, runtime, profile, trust = map(plain, (job, runtime, profile, trust))
    validate_job(job, wav)
    if request_fingerprint is not None: digest(request_fingerprint)
    _approved(profile, runtime, trust)
    authorize_signer(runtime, trust['evaluator_trust'], signer, key_id, now=now)
    measurement, execution = run_kernel(job, wav, runtime, profile,
        cancellation=cancellation, lock_root=lock_root)
    # No public sign-supplied-measurement API: this data came from our fixed run.
    validate_measurement(measurement, job, runtime['fingerprint'])
    validate_execution(execution, job, runtime, profile, measurement)
    if execution['media_sha256'] != hashlib.sha256(wav).hexdigest():
        raise AudioError('KERNEL_MEDIA_BINDING')
    if cancellation is not None and cancellation.is_set():
        raise AudioError('KERNEL_CANCELLED')
    issued = int(time.time()) if now is None else now
    integer(issued, 'issue time', 0, 2**53)
    authorize_signer(runtime, trust['evaluator_trust'], signer, key_id, now=issued)
    payload1 = {'schema_version':'bie.audio.evaluator-payload/1','key_id':key_id,
        'scope':SCOPE,'issued_at':issued,'expires_at':issued+600,
        'job_fingerprint':job['fingerprint'],'binding':job['binding'],
        'measurement':measurement,**BOUNDARIES}
    compatibility = {'schema_version':'bie.audio.signed-evaluation/1','payload':payload1,
        'signature_ed25519_hex':signer.sign(b'BIE-AUDIO-EVALUATOR-V1\0'+canonical(payload1)).hex()}
    payload = {'schema_version':'bie.audio.kernel-evaluator-payload/2', 'key_id':key_id,
        'scope':KERNEL_SCOPE,'issued_at':issued,'expires_at':issued+600,
        'profile_fingerprint':profile['fingerprint'],'execution':execution,
        'durable_request_fingerprint':request_fingerprint,
        'compatibility_receipt':compatibility,**BOUNDARIES}
    receipt = {'schema_version':SCHEMA,'payload':payload,
               'signature_ed25519_hex':signer.sign(DOMAIN+canonical(payload)).hex()}
    verify_kernel_receipt(receipt,job,runtime,profile,trust,now=issued,
                          request_fingerprint=request_fingerprint)
    return receipt


def verify_kernel_receipt(receipt, job, runtime, profile, trust, *, now=None, request_fingerprint=None):
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    validate_job(job)
    _approved(profile,runtime,trust)
    fields(receipt,('schema_version','payload','signature_ed25519_hex'),'KERNEL_RECEIPT_FIELDS')
    if receipt['schema_version'] != SCHEMA:
        raise AudioError('KERNEL_V2_RECEIPT_REQUIRED')
    payload=receipt['payload']
    fields(payload,('schema_version','key_id','scope','issued_at','expires_at',
        'profile_fingerprint','execution','durable_request_fingerprint','compatibility_receipt',*BOUNDARIES),'KERNEL_PAYLOAD_FIELDS')
    if (payload['schema_version']!='bie.audio.kernel-evaluator-payload/2'
        or payload['scope']!=KERNEL_SCOPE or payload['profile_fingerprint']!=profile['fingerprint']
        or any(type(payload[k]) is not type(v) or payload[k]!=v for k,v in BOUNDARIES.items())):
        raise AudioError('KERNEL_RECEIPT_AUTHORITY')
    if payload['durable_request_fingerprint'] is not None:
        digest(payload['durable_request_fingerprint'])
    if request_fingerprint is not None:
        digest(request_fingerprint)
        if payload['durable_request_fingerprint'] != request_fingerprint:
            raise AudioError('KERNEL_DURABLE_REQUEST_SIGNATURE_BINDING')
    issuer=next((i for i in trust['evaluator_trust']['issuers'] if i['key_id']==payload['key_id']),None)
    if issuer is None or issuer['revoked']:
        raise AudioError('KERNEL_ISSUER_UNTRUSTED')
    sig=receipt['signature_ed25519_hex']
    if type(sig) is not str or not re.fullmatch('[0-9a-f]{128}',sig):
        raise AudioError('KERNEL_SIGNATURE_FORMAT')
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(issuer['public_key_hex'])).verify(
            bytes.fromhex(sig),DOMAIN+canonical(payload))
    except (InvalidSignature,ValueError) as exc:
        raise AudioError('KERNEL_SIGNATURE_INVALID') from exc
    inner=payload['compatibility_receipt']
    measurement=verify_receipt(inner,job,trust['evaluator_trust'],now=now)
    for name in ('key_id','issued_at','expires_at'):
        if type(payload[name]) is not type(inner['payload'][name]) or payload[name]!=inner['payload'][name]:
            raise AudioError('KERNEL_INNER_RECEIPT_BINDING')
    validate_execution(payload['execution'],job,runtime,profile,measurement)
    if payload['execution']['media_sha256'] != job['binding']['media_sha256']:
        raise AudioError('KERNEL_MEDIA_BINDING')
    return measurement
