"""Independent performance evidence reinspection and conservative local QA.

Metrics are computed from complete supervisor event records and actual outputs.
A quick failed/partial render is never counted as a throughput success. No evidence
receipt is executed. Fresh, independently configured execution reviews are needed.
"""
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import hashlib
from ..release_v2.contracts import ContractError, canonical_bytes, digest, integer, sha256
from ..source_v2.models import Report, Finding
from ..source_v2.io import SnapshotStore
from ..source_v2.codec import loads
from ..repair_v2.models import Snapshot
from ..repair_v2.planner import approved
from ..repair_audit_v2.io import fields, equal, verify_files
from ..reasoning_v2.attestation import Review, ReviewVerifier
from ..video_v2.models import VideoPolicy
from ..video_v2.media import inspect_bytes
from .models import PerformanceRequest, PerformancePolicy
from .metrics import ratio, summarize

LIMITATIONS=(
 'Finite, operator-specified same-host workloads and thresholds; not production scale or a statistically calibrated SLA.',
 'Measured process wall time includes the limit launcher; queue latency includes private-copy setup and independent output verification.',
 'Linux wait4 ru_maxrss high-water accounting is not aggregate simultaneous process-tree/cgroup/GPU memory.',
 'RLIMIT_AS caps per-process virtual address space, not resident-set memory. Fixed mmap probes are not stress-tested cgroup OOM behavior.',
 'The included trusted producer queue is finite and local; no distributed broker, durability/retry/fairness/autoscaling proof.',
 'Known MP4 frame/timing checks do not establish native Remotion, audiovisual semantics or cinematic learning quality.',
 'Unsigned instrumentation needs independent provenance review; no product release or arbitrary generated-code sandbox certification.'
)
PROFILE='LINUX_WAIT4_FINITE_QUEUE_V1'
MEMORY_BASIS='LINUX_WAIT4_MAXRSS_KIB_X1024_NOT_AGGREGATE'
PROC_FIELDS={'job_id','producer_id','execution_id','enqueue_ns','dispatch_ns','process_start_ns','process_end_ns','complete_ns','exit_code','timed_out','input_unchanged','peak_rss_bytes','cpu_user_ns','cpu_system_ns','memory_basis','stdout_id','stderr_id','limits_id','outputs','issues'}

@dataclass(frozen=True,slots=True)
class Result:
    reports:tuple[Report,...]
    details_json:str
    @property
    def status(self):
        states={r.status for r in self.reports}
        return 'BLOCKED' if 'BLOCKED' in states else 'REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in states else 'CHECKS_PASSED'
    def to_dict(self):return dict(schema_version='bie.qa.performance-result/1',reports=[r.to_dict() for r in self.reports],details=loads(self.details_json.encode()),status=self.status,product_accepted=False,production_performance_certified=False)

def file_hash(name):return hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()

def review_targets(request,policy):
    return {('inventory','performance-workload'):tuple(sorted(a.artifact_id for a in request.snapshot.artifacts)),
        **({('support','performance-execution'):tuple(sorted(a.artifact_id for a in request.evidence))} if request.evidence else {})}

def inspect_output(data,spec,tools=None):
    if type(data) is not bytes or not data:raise ContractError('PERF_EMPTY_OUTPUT')
    if spec.expected_sha256 and hashlib.sha256(data).hexdigest()!=spec.expected_sha256:raise ContractError('PERF_GOLDEN_OUTPUT_MISMATCH')
    if spec.kind=='BYTES':return dict(kind='BYTES',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    vp=VideoPolicy('perf-check','0'*64,spec.width,spec.height,spec.fps_numerator,spec.fps_denominator,spec.frames,max_process_seconds=15)
    media=inspect_bytes(data,vp,tools)
    if media.frames_count!=spec.frames or media.fps!=Fraction(spec.fps_numerator,spec.fps_denominator):raise ContractError('PERF_RENDER_SPEC_MISMATCH')
    step=1/media.fps
    if media.pts[0]!=0 or any(Fraction(d)*media.time_base!=step for d in media.durations) or any(Fraction(b-a)*media.time_base!=step for a,b in zip(media.pts,media.pts[1:])):
        raise ContractError('PERF_RENDER_CLOCK_MISMATCH')
    return dict(kind='MP4',bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),frames=media.frames_count,width=media.width,height=media.height,
                fps=ratio(media.fps.numerator,media.fps.denominator),decoded_sha256=media.decode_sha256,tools_digest=media.tools_digest)

def validate_clock(row):
    names=('enqueue_ns','dispatch_ns','process_start_ns','process_end_ns','complete_ns')
    for n in names:integer(row[n],n,0,2**63-1)
    if not row['enqueue_ns']<=row['dispatch_ns']<=row['process_start_ns']<row['process_end_ns']<=row['complete_ns']:raise ContractError('PERF_CLOCK_ORDER')
    if row['complete_ns']-row['enqueue_ns']>600000000000:raise ContractError('PERF_CLOCK_RANGE')

def read_log(data):
    obj=loads(data);fields(obj,{'encoding','data'},'PERF_LOG_ENVELOPE')
    if obj['encoding']!='hex' or type(obj['data']) is not str or len(obj['data'])>131072:raise ContractError('PERF_LOG_LIMIT')
    try:b=bytes.fromhex(obj['data'])
    except ValueError as e:raise ContractError('PERF_LOG_ENCODING') from e
    if b.hex()!=obj['data']:raise ContractError('PERF_LOG_ENCODING')
    return b

def inspect_process(row,execution_id,policy,blobs,refs,used):
    fields(row,PROC_FIELDS,'PERF_PROCESS_FIELDS');validate_clock(row)
    if row['execution_id']!=execution_id+'-'+row['job_id']:raise ContractError('PERF_EXECUTION_REPLAY')
    integer(row['exit_code'],'exit_code',-255,255)
    for k in ('timed_out','input_unchanged'):
        if type(row[k]) is not bool:raise ContractError('PERF_FLAG_TYPE')
    integer(row['peak_rss_bytes'],'peak_rss_bytes',1,2**53-1)
    for k in ('cpu_user_ns','cpu_system_ns'):integer(row[k],k,0,2**63-1)
    if row['memory_basis']!=MEMORY_BASIS:raise ContractError('PERF_MEMORY_BASIS')
    if type(row['issues']) is not list or len(row['issues'])>32 or len(set(row['issues']))!=len(row['issues']) or any(type(x) is not str for x in row['issues']):raise ContractError('PERF_ISSUES_TYPE')
    for n in ('stdout_id','stderr_id','limits_id'):
        aid=row[n]
        if type(aid) is not str or aid not in blobs or refs[aid].role!='report' or aid in used:raise ContractError('PERF_LOG_REF')
        used.add(aid)
    read_log(blobs[row['stdout_id']]);read_log(blobs[row['stderr_id']])
    limits=loads(blobs[row['limits_id']])
    fields(limits,{'schema_version','execution_id','address_space','file_size','cpu','nofile','memory_scope'},'PERF_LIMIT_FIELDS')
    expected=dict(schema_version='bie.qa.performance-limits/1',execution_id=row['execution_id'],address_space=[policy.address_space_bytes]*2,
        file_size=[policy.max_file_bytes]*2,cpu=[(policy.timeout_ms+999)//1000+1]*2,nofile=[64,64],memory_scope='RLIMIT_AS_PER_PROCESS_NOT_RSS_OR_CGROUP')
    equal(limits,expected,'PERF_LIMIT_NOT_ENFORCED')
    if type(row['outputs']) is not dict:raise ContractError('PERF_OUTPUT_MAP')


def evaluate(request,root,policy,*,as_of,reviews=(),verifier=None,tools=None):
    if type(request) is not PerformanceRequest or type(policy) is not PerformancePolicy:raise ContractError('PERF_INPUT_TYPE')
    integer(as_of,'as_of');verifier=ReviewVerifier() if verifier is None else verifier
    if type(verifier) is not ReviewVerifier or type(reviews) is not tuple or len(reviews)>128 or any(type(r) is not Review for r in reviews) or len({r.review_id for r in reviews})!=len(reviews):raise ContractError('PERF_REVIEW_TYPE')
    fs=[[],[],[]];inspected=set();details={'jobs':[],'metrics':None,'authorization':{},'memory_probe':None}
    def add(indices,code,subject='performance',severity='BLOCKER'):
        for i in indices:
            f=Finding(code,severity,subject,'PERF','Performance requirement: '+code)
            if f not in fs[i]:fs[i].append(f)
    try:
        if request.snapshot.content_digest!=policy.snapshot_digest:raise ContractError('PERF_SNAPSHOT_BINDING')
        full=Snapshot(request.snapshot.run_id,request.snapshot.revision,request.snapshot.artifacts+request.evidence)
        verify_files(root,full,exact=True)
        with SnapshotStore(root) as store:blobs={a.artifact_id:store.read(a) for a in full.artifacts}
        refs={a.artifact_id:a for a in full.artifacts};inspected.update(blobs)
        if any(not set(j.input_ids)<={a.artifact_id for a in request.snapshot.artifacts} for j in policy.jobs):raise ContractError('PERF_INPUT_INVENTORY')
        targets=review_targets(request,policy)
        if any((r.purpose,r.subject_id) not in targets for r in reviews):raise ContractError('PERF_UNEXPECTED_REVIEW')
        for (purpose,subject),ids in targets.items():
            relevant=tuple(r for r in reviews if (r.purpose,r.subject_id)==(purpose,subject))
            ok,codes=approved(relevant,verifier,subject=subject,purpose=purpose,request_digest=request.content_digest,policy=policy,evidence_ids=ids,now=as_of)
            details['authorization'][subject]=dict(verified=ok,codes=codes)
            if not ok:add(range(3),'PERF_AUTHORIZATION_REQUIRED',subject,'REVIEW')
            for r in relevant:
                auth=verifier.verify_bound(r,request.content_digest,policy.content_digest,policy.max_receipt_age_seconds,as_of)
                if auth.operational and r.verdict=='REJECTED':add(range(3),'PERF_REVIEW_REJECTED',subject)
        if not request.evidence:
            add(range(3),'PERF_EXECUTION_MISSING',severity='REVIEW')
        else:
            raw=loads(blobs[request.receipt_id])
            fields(raw,{'schema_version','execution_id','snapshot_digest','policy_digest','started_at','finished_at','profile','environment_before','environment_after','collector_sha256','launcher_sha256','probe_sha256','producers','queue_start_ns','queue_end_ns','jobs','memory_probe','product_accepted','native_queue_executed'},'PERF_RECEIPT_FIELDS')
            if raw['schema_version']!='bie.qa.performance-execution/1' or raw['profile']!=PROFILE:raise ContractError('PERF_PROFILE')
            if (raw['snapshot_digest'],raw['policy_digest'])!=(request.snapshot.content_digest,policy.content_digest):raise ContractError('PERF_RECEIPT_BINDING')
            if raw['product_accepted'] is not False or raw['native_queue_executed'] is not False:raise ContractError('PERF_OVERCLAIM')
            eid=raw['execution_id']
            if type(eid) is not str or len(eid)!=37 or not eid.startswith('perf-') or any(c not in '0123456789abcdef' for c in eid[5:]):raise ContractError('PERF_EXECUTION_ID')
            for n in ('started_at','finished_at'):integer(raw[n],n)
            if not 0<=raw['finished_at']-raw['started_at']<=600 or not 0<=as_of-raw['started_at']<=policy.max_receipt_age_seconds or raw['finished_at']>as_of:raise ContractError('PERF_RECEIPT_TIME')
            for n,name in (('collector_sha256','collector.py'),('launcher_sha256','limit_exec.py'),('probe_sha256','memory_probe.py')):
                if raw[n]!=file_hash(name):raise ContractError('PERF_INSTRUMENT_IDENTITY')
            if digest(raw['environment_before'])!=policy.environment_digest or digest(raw['environment_after'])!=policy.environment_digest:raise ContractError('PERF_ENVIRONMENT_MISMATCH')
            equal(raw['producers'],[list(x) for x in policy.producer_bindings],'PERF_PRODUCER_IDENTITY')
            jobs=raw['jobs']
            if type(jobs) is not list or [j.get('job_id') for j in jobs if type(j) is dict]!=[j.job_id for j in policy.jobs] or len(jobs)!=len(policy.jobs):raise ContractError('PERF_JOB_COVERAGE')
            used={request.receipt_id};probe=raw['memory_probe']
            inspect_process(probe,eid,policy,blobs,refs,used)
            if (probe['job_id'],probe['producer_id'])!=('memoryprobe','bundled-memory-probe') or probe['outputs']:raise ContractError('PERF_MEMORY_PROBE_SCOPE')
            pr=loads(read_log(blobs[probe['stdout_id']]))
            equal(pr,dict(schema_version='bie.qa.performance-memory-probe/1',positive_allocation=True,over_limit_denied=True,address_space_limit=policy.address_space_bytes,rss_limit_tested=False),'PERF_MEMORY_PROBE_FAILED')
            if probe['exit_code'] or probe['timed_out'] or probe['issues'] or read_log(blobs[probe['stderr_id']]):raise ContractError('PERF_MEMORY_PROBE_FAILED')
            details['memory_probe']=pr
            successes=0;output_bytes=0;render_jobs=0
            for row,spec in zip(jobs,policy.jobs):
                inspect_process(row,eid,policy,blobs,refs,used)
                if row['producer_id']!=spec.producer_id:raise ContractError('PERF_JOB_PRODUCER')
                good=True;jobdetail={'job_id':spec.job_id,'outputs':[]}
                if row['exit_code']!=0:add(range(3),'PERF_JOB_FAILED',spec.job_id);good=False
                if row['timed_out']:add(range(3),'PERF_TIMEOUT',spec.job_id);good=False
                if not row['input_unchanged']:add(range(3),'PERF_INPUT_CHANGED',spec.job_id);good=False
                if row['issues']:add(range(3),'PERF_COLLECTOR_ISSUE',spec.job_id);good=False
                if row['complete_ns']-row['dispatch_ns']>policy.max_job_ms*1000000:add((0,2),'PERF_JOB_BUDGET',spec.job_id)
                if row['peak_rss_bytes']>policy.max_rss_bytes:add((1,),'PERF_MEMORY_BUDGET',spec.job_id)
                if row['process_end_ns']-row['process_start_ns']>policy.timeout_ms*1000000+1000000000 and not row['timed_out']:raise ContractError('PERF_TIMEOUT_NOT_RECORDED')
                if set(row['outputs'])!={o.output_id for o in spec.outputs}:add((0,2),'PERF_OUTPUT_COVERAGE',spec.job_id);good=False
                for o in spec.outputs:
                    aid=row['outputs'].get(o.output_id)
                    if aid is None:continue
                    if type(aid) is not str or aid not in blobs or aid in used or aid not in {a.artifact_id for a in request.evidence}:raise ContractError('PERF_OUTPUT_REF')
                    used.add(aid);data=blobs[aid];output_bytes+=len(data)
                    if refs[aid].role!=('video' if o.kind=='MP4' else 'support'):raise ContractError('PERF_OUTPUT_ROLE')
                    if len(data)>policy.max_file_bytes:add((1,),'PERF_FILE_BUDGET',spec.job_id);good=False
                    try:
                        observation=inspect_output(data,o,tools);jobdetail['outputs'].append(observation)
                        if o.kind=='MP4':
                            render_jobs+=1;dur=row['process_end_ns']-row['process_start_ns']
                            observation['render_frames_per_second']=ratio(o.frames*1000000000,dur)
                            if o.frames*1000000000000<policy.min_render_fps_milli*dur:add((0,),'PERF_RENDER_SPEED',spec.job_id)
                    except (ContractError,OSError) as exc:
                        add((0,2),exc.code if isinstance(exc,ContractError) else 'PERF_OUTPUT_IO',spec.job_id);good=False
                successes+=int(good);jobdetail['verified_success']=good;details['jobs'].append(jobdetail)
            if used!={a.artifact_id for a in request.evidence}:raise ContractError('PERF_EVIDENCE_INVENTORY')
            qstart=raw['queue_start_ns'];qend=raw['queue_end_ns']
            integer(qstart,'queue_start_ns',0,2**63-1);integer(qend,'queue_end_ns',qstart+1,2**63-1)
            if qstart!=min(r['enqueue_ns'] for r in jobs) or qend!=max(r['complete_ns'] for r in jobs) or qstart<probe['complete_ns']:raise ContractError('PERF_QUEUE_WINDOW')
            m=summarize(jobs,qstart,qend,successes);details['metrics']=m
            if m['peak_concurrency']>policy.max_workers:add((1,2),'PERF_CONCURRENCY_EXCEEDED')
            if m['p95_queue_ns']>policy.max_p95_queue_ms*1000000:add((2,),'PERF_QUEUE_LATENCY')
            if m['p95_latency_ns']>policy.max_p95_latency_ms*1000000:add((2,),'PERF_END_TO_END_LATENCY')
            if m['makespan_ns']>policy.max_batch_ms*1000000:add((2,),'PERF_BATCH_DEADLINE')
            if successes*1000000000000<policy.min_jobs_per_second_milli*m['makespan_ns']:add((2,),'PERF_THROUGHPUT')
            if successes!=len(policy.jobs):add((2,),'PERF_INCOMPLETE_WORKLOAD')
            if output_bytes>policy.max_total_output_bytes:add((1,),'PERF_TOTAL_OUTPUT_BUDGET')
            if render_jobs==0:add((0,),'PERF_RENDER_WORKLOAD_MISSING',severity='REVIEW')
        verify_files(root,full,exact=True)
    except (ContractError,OSError,UnicodeError,TypeError,KeyError,ValueError,OverflowError) as exc:
        add(range(3),exc.code if isinstance(exc,ContractError) else 'PERF_MALFORMED_OR_IO')
    add((0,),'PERF_NATIVE_RENDER_BENCHMARK_PENDING',severity='REVIEW')
    add((1,),'PERF_AGGREGATE_MEMORY_PENDING',severity='REVIEW')
    add((2,),'PERF_DISTRIBUTED_QUEUE_PENDING',severity='REVIEW')
    ev=digest(dict(request=request.content_digest,policy=policy.content_digest,verifier=verifier.configuration_digest,details=details))
    reports=tuple(Report(f'BIE-QA-PERF-{i+1:03}',request.content_digest,policy.content_digest,ev,as_of,tuple(sorted(fs[i],key=lambda f:(f.severity,f.code,f.subject_id))),
        (('jobs',len(policy.jobs)),('verified_successes',details['metrics']['verified_successes'] if details['metrics'] else 0)),tuple(sorted(inspected)),LIMITATIONS) for i in range(3))
    return Result(reports,canonical_bytes(details).decode())
