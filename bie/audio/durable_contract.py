"""H3-001: AUDIO's bounded adoption of existing canonical artifact/lease APIs.

This is a single-service-account/local-disk contract. It never grants acoustic,
model, external-service, hostile-host or whole-product acceptance.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
import importlib
import uuid
from .common import AudioError, fingerprint, integer, text
from .acoustic_contract import canonical, plain, fields, validate_job

SCOPE = 'DURABLE_LOCAL_ACOUSTIC_DIAGNOSTIC'

@dataclass(frozen=True)
class DurablePolicy:
    revision: str = 'audio-h3-durable-v1'
    lease_ttl_seconds: int = 30
    heartbeat_seconds: int = 5
    max_attempts: int = 3
    lock_timeout_seconds: int = 10
    max_files: int = 20000
    max_store_bytes: int = 2_000_000_000
    max_artifact_bytes: int = 100_000_000
    def __post_init__(self):
        text(self.revision, 'durable policy revision', 120)
        for name, low, high in (
            ('lease_ttl_seconds',3,3600), ('heartbeat_seconds',1,600),
            ('max_attempts',1,10), ('lock_timeout_seconds',1,60),
            ('max_files',20,100000), ('max_store_bytes',1_000_000,20_000_000_000),
            ('max_artifact_bytes',1024,100_000_000)):
            integer(getattr(self, name), name, low, high)
        if self.heartbeat_seconds * 2 >= self.lease_ttl_seconds:
            raise AudioError('DURABLE_HEARTBEAT_POLICY')
        if self.max_artifact_bytes > self.max_store_bytes:
            raise AudioError('DURABLE_STORAGE_POLICY')


def implementation_identity():
    # Stable code identity, not a publisher signature or a model-weight identity.
    root = Path(__file__).parent
    names = ('durable_contract.py', 'durable_store.py', 'durable_jobs.py', 'durable_pipeline.py')
    return fingerprint({name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names})


def build_request(job, *, run_id, job_id, revision, runtime_fingerprint, key_id,
                  policy=DurablePolicy()):
    validate_job(job)
    if type(policy) is not DurablePolicy:
        raise AudioError('DURABLE_POLICY_TYPE')
    try:
        if type(run_id) is not str or str(uuid.UUID(run_id)) != run_id:
            raise ValueError()
    except (ValueError, TypeError, AttributeError) as exc:
        raise AudioError('DURABLE_RUN_UUID_REQUIRED') from exc
    for value, name, limit in ((job_id,'job id',256),(revision,'revision',120),(key_id,'key id',256)):
        text(value, name, limit)
    from .common import digest
    digest(runtime_fingerprint)
    value = {'schema_version':'bie.audio.durable-request/1', 'run_id':run_id,
             'job_id':job_id, 'revision':revision, 'key_id':key_id,
             'runtime_fingerprint':runtime_fingerprint, 'job':plain(job),
             'policy':asdict(policy), 'implementation':implementation_identity(),
             'canonical_api_identity':canonical_api_identity(),
             'scope':SCOPE, 'product_accepted':False}
    value['fingerprint'] = fingerprint(value)
    return value


def validate_request(value, wav=None):
    fields(value, ('schema_version','run_id','job_id','revision','key_id',
        'runtime_fingerprint','job','policy','implementation','canonical_api_identity','scope','product_accepted','fingerprint'),
        'DURABLE_REQUEST_FIELDS')
    validate_job(value['job'], wav)
    expected = build_request(value['job'], run_id=value['run_id'], job_id=value['job_id'],
        revision=value['revision'], key_id=value['key_id'],
        runtime_fingerprint=value['runtime_fingerprint'], policy=DurablePolicy(**value['policy']))
    if canonical(value) != canonical(expected):
        raise AudioError('DURABLE_REQUEST_DRIFT')
    return DurablePolicy(**value['policy'])


def request_key(value):
    validate_request(value)
    # A changed input cannot reuse the same declared job revision silently.
    return 'AUDIO:ACOUSTIC:' + fingerprint({k:value[k] for k in ('run_id','job_id','revision')})


def canonical_api_identity():
    names = ('bie.infrastructure.artifact_store', 'bie.infrastructure.idempotency_store',
        'bie.director.director_durable_recovery', 'bie.director.director_artifacts',
        'bie.bie_core.artifact_contracts')
    return fingerprint({name:hashlib.sha256(Path(importlib.import_module(name).__file__).read_bytes()).hexdigest() for name in names})
