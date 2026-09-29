"""Operator-defined finite performance workload. No implicit quality tradeoffs.

The recipe and workload must be provisioned independently of candidate results.
Nanoseconds and bytes are integers; ratios are canonical positive rationals.
"""
from dataclasses import dataclass, asdict
from fractions import Fraction
from ..release_v2.contracts import (ArtifactRef, ContractError, token, integer,
    sha256, choice, digest, tuple_tokens, safe_relative_path)
from ..repair_v2.models import Snapshot, seq, unique

@dataclass(frozen=True, slots=True)
class OutputSpec:
    output_id: str
    path: str
    kind: str
    expected_sha256: str = ''
    width: int = 0
    height: int = 0
    frames: int = 0
    fps_numerator: int = 0
    fps_denominator: int = 1
    def __post_init__(self):
        token(self.output_id, 'output_id');safe_relative_path(self.path)
        if len(self.output_id)>24:raise ContractError('PERF_OUTPUT_ID_LENGTH')
        if self.path.split('/')[0] != 'outputs':raise ContractError('PERF_OUTPUT_ROOT')
        choice(self.kind, ('MP4','BYTES'), 'kind')
        if self.expected_sha256:sha256(self.expected_sha256,'expected_sha256')
        for n in ('width','height','frames'):integer(getattr(self,n),n,0,24000)
        integer(self.fps_numerator,'fps_numerator',0,240000)
        integer(self.fps_denominator,'fps_denominator',1,10000)
        if self.kind=='MP4':
            f=Fraction(self.fps_numerator,self.fps_denominator)
            if not (1<=self.width<=4096 and 1<=self.height<=4096 and 1<=self.frames<=24000 and 1<=f<=240):raise ContractError('PERF_MEDIA_SPEC')
            if (f.numerator,f.denominator)!=(self.fps_numerator,self.fps_denominator):raise ContractError('PERF_FPS_CANONICAL')
            if not self.path.endswith('.mp4') or self.width*self.height*self.frames*3>67108864:raise ContractError('PERF_MEDIA_BUDGET')
        elif (self.width,self.height,self.frames,self.fps_numerator,self.fps_denominator)!=(0,0,0,0,1) or not self.expected_sha256:
            raise ContractError('PERF_BYTES_REQUIRE_GOLDEN')

@dataclass(frozen=True, slots=True)
class JobSpec:
    job_id: str
    producer_id: str
    input_ids: tuple[str,...]
    outputs: tuple[OutputSpec,...]
    def __post_init__(self):
        token(self.job_id,'job_id');token(self.producer_id,'producer_id')
        if len(self.job_id)>40:raise ContractError('PERF_JOB_ID_LENGTH')
        tuple_tokens(self.input_ids,'input_ids',1,64)
        seq(self.outputs,OutputSpec,'outputs',1,4);unique(self.outputs,'output_id','outputs');unique(self.outputs,'path','outputs')

@dataclass(frozen=True, slots=True)
class PerformancePolicy:
    policy_id: str
    snapshot_digest: str
    jobs: tuple[JobSpec,...]
    producer_bindings: tuple[tuple[str,str],...]
    environment_digest: str
    max_workers: int = 2
    timeout_ms: int = 15000
    max_job_ms: int = 20000
    max_p95_queue_ms: int = 30000
    max_p95_latency_ms: int = 45000
    max_batch_ms: int = 120000
    min_jobs_per_second_milli: int = 1
    min_render_fps_milli: int = 1
    address_space_bytes: int = 536870912
    max_rss_bytes: int = 268435456
    max_file_bytes: int = 8388608
    max_total_output_bytes: int = 33554432
    max_receipt_age_seconds: int = 3600
    def __post_init__(self):
        token(self.policy_id,'policy_id');sha256(self.snapshot_digest,'snapshot_digest');sha256(self.environment_digest,'environment_digest')
        seq(self.jobs,JobSpec,'jobs',1,16);unique(self.jobs,'job_id','jobs')
        if type(self.producer_bindings) is not tuple or not 1<=len(self.producer_bindings)<=16:raise ContractError('PERF_PRODUCER_BINDINGS')
        names=[]
        for x in self.producer_bindings:
            if type(x) is not tuple or len(x)!=2:raise ContractError('PERF_PRODUCER_BINDING')
            token(x[0],'producer');sha256(x[1],'producer_digest');names.append(x[0])
        if len(names)!=len(set(names)) or set(names)!={j.producer_id for j in self.jobs}:raise ContractError('PERF_PRODUCER_COVERAGE')
        integer(self.max_workers,'max_workers',1,4)
        for n in ('timeout_ms','max_job_ms','max_p95_queue_ms','max_p95_latency_ms','max_batch_ms'):integer(getattr(self,n),n,1,300000)
        for n in ('min_jobs_per_second_milli','min_render_fps_milli'):integer(getattr(self,n),n,1,1000000000)
        integer(self.address_space_bytes,'address_space_bytes',33554432,2147483648)
        integer(self.max_rss_bytes,'max_rss_bytes',1048576,2147483648)
        integer(self.max_file_bytes,'max_file_bytes',1024,16777216)
        integer(self.max_total_output_bytes,'max_total_output_bytes',1024,50331648)
        integer(self.max_receipt_age_seconds,'max_receipt_age_seconds',1,604800)
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True, slots=True)
class PerformanceRequest:
    snapshot: Snapshot
    evidence: tuple[ArtifactRef,...] = ()
    receipt_id: str = ''
    def __post_init__(self):
        if type(self.snapshot) is not Snapshot:raise ContractError('PERF_SNAPSHOT_TYPE')
        seq(self.evidence,ArtifactRef,'evidence',0,256);unique(self.evidence,'artifact_id','evidence');unique(self.evidence,'path','evidence')
        if self.evidence:
            token(self.receipt_id,'receipt_id')
            if self.receipt_id not in {a.artifact_id for a in self.evidence if a.role=='report'}:raise ContractError('PERF_RECEIPT_REF')
        elif self.receipt_id:raise ContractError('PERF_RECEIPT_MISSING')
        if ({a.artifact_id for a in self.snapshot.artifacts}&{a.artifact_id for a in self.evidence} or
            {a.path for a in self.snapshot.artifacts}&{a.path for a in self.evidence}):raise ContractError('PERF_EVIDENCE_ALIAS')
    @property
    def content_digest(self):return digest(asdict(self))
