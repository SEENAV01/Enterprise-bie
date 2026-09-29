"""REPRO001..003: operator-owned finite rerun profile, separate from evidence.

Only a pinned trusted Python producer in a new stdlib-only virtual environment is
executed. This is a bounded reproduction profile, not dependency installation,
container reconstruction, a hostile-code sandbox or universal determinism proof.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from ..release_v2.contracts import (ArtifactRef, ContractError, token, integer,
    sha256, safe_relative_path, choice, canonical_bytes, digest)
from ..source_v2.codec import loads
from ..repair_v2.models import Snapshot, seq, unique

VERSION = 'bie.qa.repro-execution/1'
PROFILE_KEYS = {'profile', 'python_version', 'implementation', 'python_executable_sha256',
    'system', 'release', 'machine', 'byteorder', 'pointer_bits', 'isolated_prefix',
    'user_site_enabled', 'system_site_enabled', 'distributions', 'stdlib_files',
    'controlled_environment', 'hash_randomization', 'producer_protocol'}
ENV_KEYS = {'LANG','LC_ALL','TZ','PYTHONHASHSEED','PYTHONNOUSERSITE',
            'PYTHONDONTWRITEBYTECODE','SOURCE_DATE_EPOCH','BIE_REPRO_SEED'}


def profile_object(raw: str) -> dict:
    if type(raw) is not str or len(raw.encode('utf8')) > 131072:
        raise ContractError('REPRO_ENVIRONMENT_SIZE')
    obj = loads(raw.encode())
    if type(obj) is not dict or set(obj) != PROFILE_KEYS:
        raise ContractError('REPRO_ENVIRONMENT_FIELDS')
    if canonical_bytes(obj).decode() != raw:
        raise ContractError('REPRO_NONCANONICAL_PROFILE')
    if obj['profile'] != 'python-stdlib-venv-v1' or obj['producer_protocol'] != 'request-json-output-dir-v1':
        raise ContractError('REPRO_ENVIRONMENT_PROFILE')
    for key in ('python_version','implementation','system','release','machine','byteorder'):
        if type(obj[key]) is not str or not obj[key] or len(obj[key]) > 2048:
            raise ContractError('REPRO_ENVIRONMENT_VALUE',key)
    sha256(obj['python_executable_sha256'],'python_executable_sha256')
    if obj['python_executable_sha256'] == '0'*64:
        raise ContractError('REPRO_UNPINNED_INTERPRETER')
    integer(obj['pointer_bits'],'pointer_bits',32,64)
    integer(obj['hash_randomization'],'hash_randomization',0,1)
    if (obj['isolated_prefix'] is not True or obj['user_site_enabled'] is not False
        or obj['system_site_enabled'] is not False or obj['distributions'] != []):
        raise ContractError('REPRO_ENVIRONMENT_NOT_ISOLATED')
    if type(obj['stdlib_files']) is not dict or set(obj['stdlib_files']) != {'json','random','pathlib','hashlib','runpy'}:
        raise ContractError('REPRO_STDLIB_INVENTORY')
    for value in obj['stdlib_files'].values(): sha256(value,'stdlib_file')
    env = obj['controlled_environment']
    if type(env) is not dict or set(env) != ENV_KEYS or any(type(v) is not str for v in env.values()):
        raise ContractError('REPRO_CONTROLLED_ENVIRONMENT')
    return obj


@dataclass(frozen=True, slots=True)
class OutputSpec:
    artifact_id: str
    path: str
    role: str = 'support'
    golden_sha256: str = ''
    def __post_init__(self):
        token(self.artifact_id,'artifact_id'); safe_relative_path(self.path)
        if len(self.artifact_id)>96:raise ContractError('REPRO_OUTPUT_ID_LENGTH')
        choice(self.role,('source','video','game','support'),'role')
        if self.golden_sha256:
            sha256(self.golden_sha256,'golden_sha256')
            if self.golden_sha256 == '0'*64: raise ContractError('REPRO_UNPINNED_GOLDEN')
        elif type(self.golden_sha256) is not str: raise ContractError('REPRO_GOLDEN_TYPE')


@dataclass(frozen=True, slots=True)
class ReproPolicy:
    policy_id: str
    source_digest: str
    producer_id: str
    producer_artifact_id: str
    producer_sha256: str
    environment_json: str
    outputs: tuple[OutputSpec, ...]
    parameters_json: str = '{}'
    seed: int = 17
    source_date_epoch: int = 0
    repetitions: int = 2
    timeout_seconds: int = 10
    max_output_bytes: int = 16777216
    max_total_output_bytes: int = 67108864
    max_evidence_bytes: int = 4194304
    max_receipt_age_seconds: int = 3600
    def __post_init__(self):
        for n in ('policy_id','producer_id','producer_artifact_id'):token(getattr(self,n),n)
        for n in ('source_digest','producer_sha256'):
            sha256(getattr(self,n),n)
            if getattr(self,n)=='0'*64:raise ContractError('REPRO_UNPINNED_SOURCE')
        obj=profile_object(self.environment_json)
        seq(self.outputs,OutputSpec,'outputs',1,128);unique(self.outputs,'artifact_id','output_ids');unique(self.outputs,'path','output_paths')
        # Output paths must be possible simultaneously (a and a/b cannot both be files).
        paths=[s.path for s in self.outputs]
        if any(a!=b and b.startswith(a+'/') for a in paths for b in paths):raise ContractError('REPRO_OUTPUT_PREFIX_COLLISION')
        if type(self.parameters_json) is not str or len(self.parameters_json.encode())>131072:raise ContractError('REPRO_PARAMETER_SIZE')
        params=loads(self.parameters_json.encode())
        if type(params) is not dict or canonical_bytes(params).decode()!=self.parameters_json:raise ContractError('REPRO_PARAMETERS')
        integer(self.seed,'seed',0,2**32-1);integer(self.source_date_epoch,'source_date_epoch',0,2**53-1)
        integer(self.repetitions,'repetitions',2,5);integer(self.timeout_seconds,'timeout_seconds',1,60)
        integer(self.max_output_bytes,'max_output_bytes',1,16777216)
        integer(self.max_total_output_bytes,'max_total_output_bytes',self.max_output_bytes,67108864)
        integer(self.max_evidence_bytes,'max_evidence_bytes',1024,4194304)
        integer(self.max_receipt_age_seconds,'max_receipt_age_seconds',1,604800)
        expected=controlled_environment(self.seed,self.source_date_epoch)
        if obj['controlled_environment'] != expected:raise ContractError('REPRO_ENVIRONMENT_SEED_EPOCH')
        if obj['hash_randomization'] != int(self.seed!=0):raise ContractError('REPRO_HASH_SEED_CONFIGURATION')
    @property
    def content_digest(self):return digest(asdict(self))


@dataclass(frozen=True, slots=True)
class ReproRequest:
    job_id: str
    source: Snapshot
    execution: ArtifactRef
    def __post_init__(self):
        token(self.job_id,'job_id')
        if type(self.source) is not Snapshot:raise ContractError('REPRO_SNAPSHOT_TYPE')
        if type(self.execution) is not ArtifactRef or self.execution.role!='report':raise ContractError('REPRO_EXECUTION_REF')
        if self.execution.path!='execution.json' or self.execution.artifact_id!='repro-execution':raise ContractError('REPRO_EXECUTION_LOCATION')
        if self.execution.artifact_id in {a.artifact_id for a in self.source.artifacts}:raise ContractError('REPRO_EXECUTION_ALIAS')
    @property
    def content_digest(self):return digest(asdict(self))


def controlled_environment(seed,epoch):
    return dict(LANG='C',LC_ALL='C',TZ='UTC',PYTHONHASHSEED=str(seed),PYTHONNOUSERSITE='1',
        PYTHONDONTWRITEBYTECODE='1',SOURCE_DATE_EPOCH=str(epoch),BIE_REPRO_SEED=str(seed))


def binding(job_id,source,policy):
    token(job_id,'job_id')
    if type(source) is not Snapshot or type(policy) is not ReproPolicy:raise ContractError('REPRO_BINDING_TYPE')
    return dict(job_id=job_id,source_digest=source.content_digest,policy_digest=policy.content_digest,
        producer_id=policy.producer_id,producer_sha256=policy.producer_sha256)
