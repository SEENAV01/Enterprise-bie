"""Inspect rerun evidence and all emitted bytes; finite equality is not quality."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib, os, stat
from ..release_v2.contracts import ContractError,ArtifactRef,canonical_bytes,digest,integer,token
from ..source_v2.io import SnapshotStore
from ..source_v2.codec import loads
from ..source_v2.models import Report,Finding
from ..repair_v2.codec import decode
from ..repair_v2.planner import approved
from ..repair_audit_v2.io import fields,equal,verify_files
from ..reasoning_v2.attestation import Review,ReviewVerifier
from .models import ReproRequest,ReproPolicy,VERSION,binding,profile_object
from .runner import inspect_source,implementation_digest
from .environment import PROBE

LIMITS=(
 'Finite identical outputs do not prove universal determinism or educational correctness.',
 'Fresh no-pip Python venv profile only; no third-party dependency/OS/container/GPU rebuild.',
 'Measured interpreter and selected stdlib bytes are not complete transitive dependency closure.',
 'Execution receipts require independent trust; local trusted producers are not hostile-code sandboxes.',
 'Exact artifact bytes are compared without normalization, ignored fields or substituted hashes.',
 'No native Remotion/game, cross-machine claim, Section15 acceptance or product release.'
)

@dataclass(frozen=True,slots=True)
class Result:
    reports: tuple[Report,...]
    details_json: str
    @property
    def status(self):
        states={r.status for r in self.reports}
        return 'BLOCKED' if 'BLOCKED' in states else 'REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in states else 'CHECKS_PASSED'
    def to_dict(self):return dict(schema_version='bie.qa.repro-result/1',reports=[r.to_dict() for r in self.reports],
        details=loads(self.details_json.encode()),status=self.status,product_accepted=False,full_product_reproduced=False,cross_machine_verified=False)


def _process(p,timeout,code):
    fields(p,{'started','process_exit','error','wall_started_ns','wall_finished_ns','elapsed_ms'},'REPRO_PROCESS_FIELDS')
    if p['started'] is not True or type(p['process_exit']) is not int or p['process_exit']!=0 or p['error']!='':raise ContractError(code)
    for k in ('wall_started_ns','wall_finished_ns'):integer(p[k],k,1,2**63-1)
    integer(p['elapsed_ms'],'elapsed_ms',0,(timeout+5)*1000)
    if p['wall_finished_ns']<p['wall_started_ns']:raise ContractError('REPRO_PROCESS_CLOCK')


def compare_outputs(all_rows,policy):
    """Compares independently inspected output bytes, not merely receipt SHA claims."""
    if len(all_rows)!=policy.repetitions:raise ContractError('REPRO_COMPARISON_COVERAGE')
    mismatches=[];golden=[]
    for i,rows in enumerate(all_rows):
        if len(rows)!=len(policy.outputs):raise ContractError('REPRO_HASH_OUTPUT_COVERAGE')
        for j,((ref,data),spec) in enumerate(zip(rows,policy.outputs)):
            if (ref.role,ref.path)!=(spec.role,f'run-{i+1:02}/output/'+spec.path):raise ContractError('REPRO_HASH_PATH_ROLE')
            if data!=all_rows[0][j][1]:mismatches.append((i+1,spec.artifact_id))
            if spec.golden_sha256 and hashlib.sha256(data).hexdigest()!=spec.golden_sha256:golden.append((i+1,spec.artifact_id))
    return mismatches,golden


def evaluate(request,source_root,evidence_root,policy,*,as_of,reviews=(),verifier=None):
    if type(request) is not ReproRequest or type(policy) is not ReproPolicy:raise ContractError('REPRO_INPUT_TYPE')
    integer(as_of,'as_of');verifier=ReviewVerifier() if verifier is None else verifier
    if type(reviews) is not tuple or any(type(r) is not Review for r in reviews) or len(reviews)>128 or len({r.review_id for r in reviews})!=len(reviews):raise ContractError('REPRO_REVIEW_COLLECTION')
    fs=[[],[],[]];inspected=set();measure=[[],[],[]];detail={};seen_files=set();recheck=[]
    def add(indices,code,subject='rerun',severity='BLOCKER'):
        for i in indices:
            f=Finding(code,severity,subject,'QA','Reproducibility requirement: '+code)
            if f not in fs[i]:fs[i].append(f)
    def auth(subject,purpose,ids):
        relevant=tuple(r for r in reviews if (r.subject_id,r.purpose)==(subject,purpose))
        ok,codes=approved(relevant,verifier,subject=subject,purpose=purpose,request_digest=request.content_digest,
            policy=policy,evidence_ids=ids,now=as_of)
        if not ok:add(range(3),'REPRO_AUTHORIZATION_REQUIRED',subject,'REVIEW')
    def readref(store,obj,aid,path,role='report'):
        r=decode(obj,ArtifactRef)
        if (r.artifact_id,r.path,r.role)!=(aid,path,role):raise ContractError('REPRO_EVIDENCE_LOCATION')
        if r.path in seen_files:raise ContractError('REPRO_EVIDENCE_REUSED')
        data=store.read(r);inspected.add(aid);seen_files.add(r.path);recheck.append(r)
        return r,data
    try:
        a=Path(source_root).resolve();b=Path(evidence_root).resolve()
        if a==b or a.is_relative_to(b) or b.is_relative_to(a):raise ContractError('REPRO_ROOT_OVERLAP')
        inspect_source(request.source,source_root,policy);inspected.update(x.artifact_id for x in request.source.artifacts)
        targets={('repro-inventory','inventory'),('repro-execution','support')}
        if any((r.subject_id,r.purpose) not in targets for r in reviews):raise ContractError('REPRO_UNEXPECTED_REVIEW')
        auth('repro-inventory','inventory',tuple(sorted(a.artifact_id for a in request.source.artifacts)))
        if request.execution.size>policy.max_evidence_bytes:raise ContractError('REPRO_RECEIPT_SIZE')
        with SnapshotStore(evidence_root) as store:
            raw=store.read(request.execution);seen_files.add(request.execution.path);inspected.add(request.execution.artifact_id);recheck.append(request.execution)
        receipt=loads(raw)
        fields(receipt,{'schema_version','binding','evaluated_at','collector_digest','probe_digest','runs','execution_profile',
            'hostile_code_sandbox','cross_machine_verified','full_product_reproduced','product_accepted'},'REPRO_RECEIPT_FIELDS')
        if receipt['schema_version']!=VERSION or receipt['execution_profile']!='fresh-stdlib-venv-trusted-producer':raise ContractError('REPRO_RECEIPT_SCHEMA')
        if any(receipt[k] is not False for k in ('hostile_code_sandbox','cross_machine_verified','full_product_reproduced','product_accepted')):raise ContractError('REPRO_SCOPE_CLAIM')
        equal(receipt['binding'],binding(request.job_id,request.source,policy),'REPRO_RECEIPT_BINDING')
        equal(receipt['collector_digest'],implementation_digest(),'REPRO_COLLECTOR_IDENTITY')
        equal(receipt['probe_digest'],hashlib.sha256(PROBE.encode()).hexdigest(),'REPRO_PROBE_IDENTITY')
        integer(receipt['evaluated_at'],'evaluated_at')
        if not 0<=as_of-receipt['evaluated_at']<=policy.max_receipt_age_seconds:raise ContractError('REPRO_RECEIPT_STALE')
        if type(receipt['runs']) is not list or len(receipt['runs'])!=policy.repetitions:raise ContractError('REPRO_RUN_COVERAGE')
        auth('repro-execution','support',(request.execution.artifact_id,))
        collected=[];execution_ids=set();previous_end=0;details=[]
        for index,row in enumerate(receipt['runs'],1):
            tag=f'run-{index:02}'
            fields(row,{'index','execution_id','evaluated_at','source_digest','bootstrap','process','probe_before_process',
                'probe_after_process','error','environment_before','environment_after','logs','venv_config','outputs'},'REPRO_RUN_FIELDS')
            equal((row['index'],row['evaluated_at'],row['source_digest']),(index,receipt['evaluated_at'],request.source.content_digest),'REPRO_RUN_BINDING')
            token(row['execution_id'],'execution_id')
            if row['execution_id'] in execution_ids:raise ContractError('REPRO_EXECUTION_REUSED')
            execution_ids.add(row['execution_id'])
            if type(row['error']) is not str:raise ContractError('REPRO_ERROR_TYPE')
            if row['error']:
                add(range(3),row['error'],tag);collected.append([]);continue
            _process(row['bootstrap'],30,'REPRO_ENVIRONMENT_NOT_CREATED')
            _process(row['process'],policy.timeout_seconds,'REPRO_PRODUCER_NOT_EXECUTED')
            _process(row['probe_before_process'],10,'REPRO_PROFILE_NOT_MEASURED')
            _process(row['probe_after_process'],10,'REPRO_PROFILE_NOT_MEASURED')
            ordered=[row[k] for k in ('bootstrap','probe_before_process','process','probe_after_process')]
            for p in ordered:
                if p['wall_started_ns']<previous_end:raise ContractError('REPRO_PROCESS_ORDER')
                previous_end=p['wall_finished_ns']
            with SnapshotStore(evidence_root) as store:
                _,before=readref(store,row['environment_before'],tag+'-environment-before',tag+'/environment-before.json')
                _,after=readref(store,row['environment_after'],tag+'-environment-after',tag+'/environment-after.json')
                if canonical_bytes(loads(before)).decode()!=policy.environment_json:raise ContractError('REPRO_ENVIRONMENT_MISMATCH')
                if before!=after:raise ContractError('REPRO_ENVIRONMENT_MUTATED')
                profile_object(before.decode())
                _,cfg=readref(store,row['venv_config'],tag+'-venv-config',tag+'/pyvenv.cfg')
                kv={}
                for line in cfg.decode('utf8').splitlines():
                    if '=' not in line:continue
                    k,v=(x.strip().lower() for x in line.split('=',1))
                    if k in kv:raise ContractError('REPRO_VENV_CONFIG_DUPLICATE')
                    kv[k]=v
                if kv.get('include-system-site-packages')!='false':raise ContractError('REPRO_VENV_SYSTEM_PACKAGES')
                _,logs=readref(store,row['logs'],tag+'-logs',tag+'/logs.json');logs=loads(logs)
                fields(logs,{'stdout','stderr'},'REPRO_LOG_FIELDS')
                for v in logs.values():
                    fields(v,{'size','sha256','hex'},'REPRO_LOG_ENTRY')
                    integer(v['size'],'log_size',0,1048576)
                    if type(v['hex']) is not str or len(v['hex'])!=2*v['size']:raise ContractError('REPRO_LOG_BYTES')
                    try:blob=bytes.fromhex(v['hex'])
                    except ValueError as e:raise ContractError('REPRO_LOG_ENCODING') from e
                    if len(blob)!=v['size'] or hashlib.sha256(blob).hexdigest()!=v['sha256']:raise ContractError('REPRO_LOG_HASH')
            if type(row['outputs']) is not list or len(row['outputs'])!=len(policy.outputs):raise ContractError('REPRO_OUTPUT_INVENTORY')
            out=[]
            with SnapshotStore(evidence_root) as store:
                for obj,spec in zip(row['outputs'],policy.outputs):
                    ref,data=readref(store,obj,tag+'-out-'+spec.artifact_id,tag+'/output/'+spec.path,spec.role)
                    if ref.size>policy.max_output_bytes:raise ContractError('REPRO_OUTPUT_SIZE')
                    out.append((ref,data))
            if sum(r.size for r,_ in out)>policy.max_total_output_bytes:raise ContractError('REPRO_OUTPUT_TOTAL_SIZE')
            collected.append(out);details.append(dict(index=index,output_sha256={s.artifact_id:r.sha256 for (r,_),s in zip(out,policy.outputs)}))
        if all(collected) and len(collected)==policy.repetitions:
            mismatches,golden=compare_outputs(collected,policy)
            for i,aid in mismatches:add((0,2),'REPRO_OUTPUT_BYTES_DIFFER',f'run-{i:02}:'+aid)
            for i,aid in golden:add((2,),'REPRO_GOLDEN_HASH_MISMATCH',f'run-{i:02}:'+aid)
            measure[0]=[('executed_reruns',len(collected))]
            measure[1]=[('fresh_environments_matched',len(collected))]
            measure[2]=[('artifact_comparisons',(len(collected)-1)*len(policy.outputs)),('golden_checks',sum(bool(x.golden_sha256) for x in policy.outputs)*len(collected))]
        detail=dict(runs=details,repetitions_required=policy.repetitions,comparison='EXACT_BYTES_NO_NORMALIZATION',environment_scope='FRESH_STDLIB_VENV_SAME_HOST')
        # Detect hidden evidence or untracked files; known failed runs may preserve partial evidence.
        if not any(row['error'] for row in receipt['runs']):
            actual=set()
            for base,dirs,files in os.walk(b,followlinks=False):
                for name in dirs+files:
                    p=Path(base)/name;s=p.lstat()
                    if stat.S_ISLNK(s.st_mode) or not (stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode)):raise ContractError('REPRO_UNSAFE_EVIDENCE')
                    if stat.S_ISREG(s.st_mode):actual.add(p.relative_to(b).as_posix())
            if actual!=seen_files:raise ContractError('REPRO_EXTRA_OR_MISSING_EVIDENCE')
        verify_files(source_root,request.source,exact=True)
        for ref in recheck:
            with SnapshotStore(evidence_root) as st:st.read(ref)
    except (ContractError,OSError,UnicodeError) as ex:
        add(range(3),ex.code if isinstance(ex,ContractError) else 'REPRO_INPUT_IO')
    evidence_digest=digest(dict(request=request.content_digest,policy=policy.content_digest,verifier=verifier.configuration_digest))
    reports=tuple(Report(f'BIE-QA-REPRO-{i+1:03}',request.content_digest,policy.content_digest,evidence_digest,as_of,
        tuple(sorted(fs[i],key=lambda f:(f.severity,f.code,f.subject_id))),tuple(measure[i]),tuple(sorted(inspected)),LIMITS) for i in range(3))
    return Result(reports,canonical_bytes(detail).decode())
