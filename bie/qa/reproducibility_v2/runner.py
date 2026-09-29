"""Execute identical approved inputs in independently rebuilt private environments.

Never loads executable paths from evidence. The operator policy pins the script
already inside the source snapshot. The resulting receipt is unsigned. Executed
producer code must be trusted: local resource bounds are NOT hostile isolation.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import asdict
import hashlib, os, shutil, stat, sys, tempfile, uuid
from ..release_v2.contracts import ArtifactRef,ContractError,canonical_bytes,integer,digest,token
from ..source_v2.io import SnapshotStore
from ..source_v2.codec import loads
from ..repair_audit_v2.io import copy_snapshot,verify_files,write_new
from .models import ReproPolicy,ReproRequest,VERSION,binding,profile_object
from .environment import new_environment,measure,run_process,file_digest,PROBE


def implementation_digest():
    return digest({p.name:file_digest(p) for p in sorted(Path(__file__).parent.glob('*.py'))})


def inspect_source(source,source_root,policy):
    if type(policy) is not ReproPolicy or source.content_digest!=policy.source_digest:
        raise ContractError('REPRO_SOURCE_POLICY_BINDING')
    verify_files(source_root,source,exact=True)
    producer=next((a for a in source.artifacts if a.artifact_id==policy.producer_artifact_id),None)
    if producer is None or producer.sha256!=policy.producer_sha256 or not producer.path.endswith('.py'):
        raise ContractError('REPRO_PRODUCER_IDENTITY')
    return producer


def persist(root,path,payload,aid,role='report'):
    dest=Path(root)/path;dest.parent.mkdir(parents=True,exist_ok=True)
    if type(payload) is not bytes or not payload:raise ContractError('REPRO_EMPTY_EVIDENCE')
    write_new(dest,payload)
    return ArtifactRef(aid,path,hashlib.sha256(payload).hexdigest(),len(payload),role)


def inventory(root,policy):
    """Read actual file set, reject links/special files, enforce exact output inventory."""
    root=Path(root);found=set()
    if root.is_symlink() or not root.is_dir():raise ContractError('REPRO_UNSAFE_OUTPUT_ROOT')
    for base,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            p=Path(base)/name;s=p.lstat()
            if stat.S_ISLNK(s.st_mode):raise ContractError('REPRO_UNSAFE_OUTPUT')
            if stat.S_ISDIR(s.st_mode):continue
            if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1:raise ContractError('REPRO_UNSAFE_OUTPUT')
            found.add(p.relative_to(root).as_posix())
    if found!={s.path for s in policy.outputs}:raise ContractError('REPRO_OUTPUT_INVENTORY')
    refs=[]
    for spec in policy.outputs:
        p=root/spec.path;size=p.stat().st_size
        if not 1<=size<=policy.max_output_bytes:raise ContractError('REPRO_OUTPUT_SIZE')
        refs.append(ArtifactRef(spec.artifact_id,spec.path,file_digest(p),size,spec.role))
    if sum(r.size for r in refs)>policy.max_total_output_bytes:raise ContractError('REPRO_OUTPUT_TOTAL_SIZE')
    with SnapshotStore(root) as st:return [(r,st.read(r)) for r in refs]


def _one(index,job_id,source,source_root,producer,policy,python,evidence,parent,as_of):
    tag=f'run-{index:02}';runroot=Path(parent)/tag;runroot.mkdir()
    private=copy_snapshot(source_root,source,runroot)
    original_job=canonical_bytes(dict(schema_version='bie.qa.repro-job/1',job_id=job_id,
        seed=policy.seed,source_date_epoch=policy.source_date_epoch,parameters=loads(policy.parameters_json.encode()),
        input_directory=str(private),source_digest=source.content_digest))
    job=runroot/'request.json';job.write_bytes(original_job)
    outputs=runroot/'output';outputs.mkdir()
    row=dict(index=index,execution_id='repro-'+uuid.uuid4().hex,evaluated_at=as_of,source_digest=source.content_digest,
        bootstrap=None,process=None,probe_before_process=None,probe_after_process=None,error='',
        environment_before=None,environment_after=None,logs=None,venv_config=None,outputs=[])
    try:
        exe,env,bootstrap,_=new_environment(runroot/'environment',python,policy.seed,policy.source_date_epoch)
        row['bootstrap']=bootstrap
        before,p_before=measure(exe,env,runroot/'probe-before');row['probe_before_process']=p_before
        row['environment_before']=asdict(persist(evidence,tag+'/environment-before.json',canonical_bytes(before),tag+'-environment-before'))
        if canonical_bytes(before).decode()!=policy.environment_json:raise ContractError('REPRO_ENVIRONMENT_MISMATCH')
        # Raw venv configuration proves only what was read; environment review still required.
        cfg=(exe.parent.parent/'pyvenv.cfg').read_bytes()
        row['venv_config']=asdict(persist(evidence,tag+'/pyvenv.cfg',cfg,tag+'-venv-config'))
        process,logs=run_process([str(exe),'-s','-B','-P',str(private/producer.path),str(job),str(outputs)],
            private,env,policy.timeout_seconds,runroot/'producer-logs')
        row['process']=process
        logdata={n:dict(size=len(v),sha256=hashlib.sha256(v).hexdigest(),hex=v.hex()) for n,v in logs.items()}
        row['logs']=asdict(persist(evidence,tag+'/logs.json',canonical_bytes(logdata),tag+'-logs'))
        after,p_after=measure(exe,env,runroot/'probe-after');row['probe_after_process']=p_after
        row['environment_after']=asdict(persist(evidence,tag+'/environment-after.json',canonical_bytes(after),tag+'-environment-after'))
        if canonical_bytes(after)!=canonical_bytes(before):raise ContractError('REPRO_ENVIRONMENT_MUTATED')
        if job.read_bytes()!=original_job:raise ContractError('REPRO_JOB_MUTATED')
        verify_files(private,source,exact=True)
        if process['error']:raise ContractError(process['error'])
        if process['process_exit']!=0:raise ContractError('REPRO_PRODUCER_EXIT')
        for ref,data in inventory(outputs,policy):
            exported=persist(evidence,tag+'/output/'+ref.path,data,tag+'-out-'+ref.artifact_id,ref.role)
            row['outputs'].append(asdict(exported))
        verify_files(private,source,exact=True)
    except (ContractError,OSError) as ex:
        row['error']=ex.code if isinstance(ex,ContractError) else 'REPRO_EXECUTION_IO'
    finally:
        shutil.rmtree(runroot,ignore_errors=True)
    return row


def collect(job_id,source,source_root,evidence_root,policy,*,as_of,python=getattr(sys,"_base_executable",sys.executable)):
    """Run the approved producer 2..5 times. Never installs third-party packages.

    evidence_root must be new and outside source_root. A failure is preserved in
    execution.json and does not manufacture successful runs or delete evidence.
    """
    integer(as_of,'as_of');token(job_id,'job_id')
    producer=inspect_source(source,source_root,policy)
    sr=Path(source_root).resolve();er=Path(evidence_root).resolve()
    if sr==er or sr.is_relative_to(er) or er.is_relative_to(sr):raise ContractError('REPRO_ROOT_OVERLAP')
    if Path(evidence_root).is_symlink() or er.exists():raise ContractError('REPRO_NEW_EVIDENCE_ROOT_REQUIRED')
    exe=Path(python).resolve()
    if file_digest(exe)!=profile_object(policy.environment_json)['python_executable_sha256']:
        raise ContractError('REPRO_INTERPRETER_IDENTITY')
    er.mkdir(parents=True,mode=0o700)
    initial_impl=implementation_digest()
    with tempfile.TemporaryDirectory(prefix='bie-repro-run-') as parent:
        runs=[_one(i,job_id,source,sr,producer,policy,str(exe),er,parent,as_of) for i in range(1,policy.repetitions+1)]
    verify_files(sr,source,exact=True)
    if implementation_digest()!=initial_impl:raise ContractError('REPRO_COLLECTOR_CHANGED')
    receipt=dict(schema_version=VERSION,binding=binding(job_id,source,policy),evaluated_at=as_of,
        collector_digest=initial_impl,probe_digest=hashlib.sha256(PROBE.encode()).hexdigest(),
        runs=runs,execution_profile='fresh-stdlib-venv-trusted-producer',hostile_code_sandbox=False,
        cross_machine_verified=False,full_product_reproduced=False,product_accepted=False)
    data=canonical_bytes(receipt)
    if len(data)>policy.max_evidence_bytes:raise ContractError('REPRO_RECEIPT_SIZE')
    ref=persist(er,'execution.json',data,'repro-execution')
    return ReproRequest(job_id,source,ref)
