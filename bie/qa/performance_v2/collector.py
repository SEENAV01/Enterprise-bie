"""Real finite local job queue with wait4 memory/timing collection.

Only independently provisioned, pinned TRUSTED producers are executed. This is
not a generated-code sandbox or a replacement for the canonical queue. No shell,
network fetch, dependency install or command execution from evidence JSON.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor
import os, sys, platform, hashlib, time, uuid, json, signal, selectors, subprocess, threading, stat
from decimal import Decimal
from ..release_v2.contracts import ContractError, ArtifactRef, token, sha256, digest, canonical_bytes
from ..source_v2.io import SnapshotStore
from ..repair_audit_v2.io import verify_files, write_new
from .models import PerformancePolicy, PerformanceRequest
from .evaluator import PROFILE, MEMORY_BASIS, file_hash, inspect_output

@dataclass(frozen=True, slots=True)
class Producer:
    producer_id: str
    executable: str
    executable_sha256: str
    arguments: tuple[str,...]
    def __post_init__(self):
        token(self.producer_id,'producer_id');sha256(self.executable_sha256,'executable_sha256')
        if type(self.executable) is not str or not Path(self.executable).is_absolute():raise ContractError('PERF_ABSOLUTE_EXECUTABLE')
        if type(self.arguments) is not tuple or not 1<=len(self.arguments)<=128 or any(type(s) is not str or '\0' in s or len(s)>4096 for s in self.arguments):raise ContractError('PERF_ARGUMENTS')
    @property
    def content_digest(self):return digest(asdict(self))
    def verify(self):
        p=Path(self.executable)
        if not p.is_file() or not os.access(p,os.X_OK) or hashlib.sha256(p.read_bytes()).hexdigest()!=self.executable_sha256:raise ContractError('PERF_PRODUCER_CHANGED')

def capture_environment():
    if sys.platform!='linux' or not hasattr(os,'wait4'):raise ContractError('PERF_LINUX_REQUIRED')
    p=Path(getattr(sys,'_base_executable',sys.executable)).resolve()
    return dict(profile='SELECTED_SAME_HOST_CPU_ENVIRONMENT_V1',system=platform.system(),machine=platform.machine(),kernel=platform.release(),
        python=platform.python_version(),python_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),cpu_count=os.cpu_count() or 1,
        cpu_affinity=sorted(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else [],
        locale='C.UTF-8',omp_threads='1',python_hash_seed='0',full_dependency_closure_verified=False)

def _cpu_ns(value):return int(Decimal(str(value))*1000000000)

def _limit_evidence(path, issues):
    """Preserve a bounded failure witness; never synthesize installed limits."""
    path=Path(path);raw=b'';failure=None
    try:
        if not path.exists():failure='PERF_LIMITS_MISSING'
        elif path.is_symlink() or not path.is_file() or path.stat().st_nlink!=1:
            failure='PERF_LIMITS_UNSAFE'
        elif path.stat().st_size>65536:failure='PERF_LIMITS_OVERSIZED'
        else:
            raw=path.read_bytes()
            if not raw:failure='PERF_LIMITS_EMPTY'
            else:
                from ..source_v2.codec import loads
                try:
                    obj=loads(raw)
                    if type(obj) is not dict:failure='PERF_LIMITS_MALFORMED'
                except (ValueError,TypeError,UnicodeError):failure='PERF_LIMITS_MALFORMED'
    except OSError:failure='PERF_LIMITS_UNAVAILABLE'
    if failure is None:return raw
    issues.append(failure)
    return canonical_bytes({'schema_version':'bie.qa.failed-limit-evidence/1',
        'status':'UNAVAILABLE','failure':failure,'raw_bytes':len(raw),
        'raw_sha256':hashlib.sha256(raw).hexdigest()})


def run_program(producer,argv,work,policy,execution_id,origin):
    """No preexec_fn: the limit installer execs the approved binary in its own PID."""
    producer.verify();work=Path(work)
    env={'PATH':'/usr/bin:/bin','HOME':str(work),'TMPDIR':str(work),'LC_ALL':'C.UTF-8','LANG':'C.UTF-8',
         'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','PYTHONHASHSEED':'0','PYTHONDONTWRITEBYTECODE':'1'}
    cfg=dict(argv=argv,executable_sha256=producer.executable_sha256,address_space_bytes=policy.address_space_bytes,
        cpu_seconds=(policy.timeout_ms+999)//1000+1,max_file_bytes=policy.max_file_bytes,execution_id=execution_id,env=env)
    config=work/'launcher.json';limits=work/'limits.json';config.write_bytes(canonical_bytes(cfg))
    launcher=Path(__file__).with_name('limit_exec.py').resolve()
    python=str(Path(getattr(sys,'_base_executable',sys.executable)).resolve())
    start=time.monotonic_ns()-origin
    p=subprocess.Popen([python,'-I','-B','-S',str(launcher),str(config),str(limits)],cwd=work,env=env,
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True,start_new_session=True)
    sel=selectors.DefaultSelector();out=bytearray();err=bytearray();timeout=False;issues=[];usage=None;status=None
    deadline=origin+start+policy.timeout_ms*1000000
    try:
        for pipe,name in ((p.stdout,'stdout'),(p.stderr,'stderr')):
            os.set_blocking(pipe.fileno(),False);sel.register(pipe,selectors.EVENT_READ,name)
        while usage is None or sel.get_map():
            if time.monotonic_ns()>deadline:
                timeout=True;issues.append('PERF_PROCESS_TIMEOUT');break
            for key,_ in sel.select(0.005):
                b=os.read(key.fileobj.fileno(),16384)
                if not b:sel.unregister(key.fileobj);continue
                dest=out if key.data=='stdout' else err
                if len(dest)+len(b)>65536:
                    dest.extend(b[:max(0,65536-len(dest))]);issues.append('PERF_PROCESS_LOG_LIMIT');break
                dest.extend(b)
            if issues:break
            if usage is None:
                pid,s,u=os.wait4(p.pid,os.WNOHANG)
                if pid:status=s;usage=u;p.returncode=os.waitstatus_to_exitcode(s)
        if usage is None or issues:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        if usage is None:
            _,status,usage=os.wait4(p.pid,0);p.returncode=os.waitstatus_to_exitcode(status)
        finish=time.monotonic_ns()-origin
    finally:
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        if usage is None:
            _,status,usage=os.wait4(p.pid,0);p.returncode=os.waitstatus_to_exitcode(status)
        sel.close();p.stdout.close();p.stderr.close()
    producer.verify()
    limit_bytes=_limit_evidence(limits,issues)
    return dict(process_start_ns=start,process_end_ns=finish,exit_code=p.returncode,timed_out=timeout,
        peak_rss_bytes=int(usage.ru_maxrss)*1024,cpu_user_ns=_cpu_ns(usage.ru_utime),cpu_system_ns=_cpu_ns(usage.ru_stime),
        memory_basis=MEMORY_BASIS,issues=issues),bytes(out),bytes(err),limit_bytes

def collect(request,root,policy,producers,*,tools=None):
    if type(request) is not PerformanceRequest or request.evidence or type(policy) is not PerformancePolicy:raise ContractError('PERF_COLLECT_INPUT')
    if request.snapshot.content_digest!=policy.snapshot_digest:raise ContractError('PERF_SNAPSHOT_BINDING')
    if type(producers) is not tuple or any(type(x) is not Producer for x in producers):raise ContractError('PERF_PRODUCER_REGISTRY')
    registry={p.producer_id:p for p in producers}
    if len(registry)!=len(producers) or tuple((pid,registry[pid].content_digest) for pid,_ in policy.producer_bindings if pid in registry)!=policy.producer_bindings or set(registry)!={p for p,_ in policy.producer_bindings}:raise ContractError('PERF_PRODUCER_REGISTRY')
    before=capture_environment()
    if digest(before)!=policy.environment_digest:raise ContractError('PERF_ENVIRONMENT_MISMATCH')
    for p in producers:p.verify()
    verify_files(root,request.snapshot,exact=True)
    root=Path(root);snapshot=request.snapshot
    with SnapshotStore(root) as store:inputs={a.artifact_id:store.read(a) for a in snapshot.artifacts}
    if any(not set(j.input_ids)<=inputs.keys() for j in policy.jobs):raise ContractError('PERF_INPUT_INVENTORY')
    execution_id='perf-'+uuid.uuid4().hex;relative='perf_evidence/'+execution_id
    target=root/relative;target.mkdir(parents=True,exist_ok=False)
    started_at=time.time_ns()//1000000000;origin=time.monotonic_ns();evidence=[];lock=threading.Lock()
    def publish(name,data,role='report'):
        if type(data) is not bytes:raise ContractError('PERF_PUBLISH_BYTES')
        path=target/name;path.parent.mkdir(parents=True,exist_ok=True);write_new(path,data)
        aid='p21-'+execution_id[5:17]+'-'+name.replace('/','-').replace('.','-')
        a=ArtifactRef(aid,relative+'/'+name,hashlib.sha256(data).hexdigest(),len(data),role)
        with lock:evidence.append(a)
        return a.artifact_id
    def record_process(job_id,producer,argv,work,enqueued,dispatch):
        record,out,err,limits=run_program(producer,argv,work,policy,execution_id+'-'+job_id,origin)
        return dict(job_id=job_id,producer_id=producer.producer_id,execution_id=execution_id+'-'+job_id,enqueue_ns=enqueued,dispatch_ns=dispatch,
            **record,input_unchanged=True,stdout_id=publish(job_id+'/stdout.json',canonical_bytes({'encoding':'hex','data':out.hex()})),stderr_id=publish(job_id+'/stderr.json',canonical_bytes({'encoding':'hex','data':err.hex()})),
            limits_id=publish(job_id+'/limits.json',limits),outputs={})
    # Fixed probe, outside the queue denominator; both positive and denial controls.
    with TemporaryDirectory(prefix='bie-perf-probe-') as td:
        python=str(Path(getattr(sys,'_base_executable',sys.executable)).resolve())
        pp=Producer('bundled-memory-probe',python,hashlib.sha256(Path(python).read_bytes()).hexdigest(),('-I','-B','-S',str(Path(__file__).with_name('memory_probe.py').resolve())))
        now=time.monotonic_ns()-origin
        probe=record_process('memoryprobe',pp,[pp.executable,*pp.arguments],td,now,now)
        probe['complete_ns']=time.monotonic_ns()-origin
    qstart=time.monotonic_ns()-origin
    def job(spec):
        dispatch=time.monotonic_ns()-origin
        with TemporaryDirectory(prefix='bie-perf-job-') as td:
            work=Path(td);mapping={};initial={}
            for aid in spec.input_ids:
                path=work/'inputs'/aid;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(inputs[aid]);mapping[aid]=str(path);initial[path]=hashlib.sha256(inputs[aid]).hexdigest()
            outputs={o.output_id:work/o.path for o in spec.outputs}
            for p in outputs.values():p.parent.mkdir(parents=True,exist_ok=True)
            producer=registry[spec.producer_id];args=[]
            for s in producer.arguments:
                if s.startswith('{input:') and s.endswith('}'):
                    key=s[7:-1]
                    if key not in mapping:raise ContractError('PERF_ARGUMENT_INPUT')
                    args.append(mapping[key])
                elif s.startswith('{output:') and s.endswith('}'):
                    key=s[8:-1]
                    if key not in outputs:raise ContractError('PERF_ARGUMENT_OUTPUT')
                    args.append(str(outputs[key]))
                elif '{' in s or '}' in s:raise ContractError('PERF_ARGUMENT_PLACEHOLDER')
                else:args.append(s)
            row=record_process(spec.job_id,producer,[producer.executable,*args],work,qstart,dispatch)
            row['input_unchanged']=all(p.is_file() and not p.is_symlink() and p.stat().st_nlink==1 and hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in initial.items())
            expected=set(initial)|set(outputs.values())|{work/'limits.json',work/'launcher.json'}
            actual=set()
            for p in work.rglob('*'):
                if p.is_symlink() or (not p.is_dir() and (not p.is_file() or p.lstat().st_nlink!=1)):
                    row['issues'].append('PERF_UNSAFE_WORKSPACE');continue
                if p.is_file():actual.add(p)
            if actual-expected:row['issues'].append('PERF_UNEXPECTED_WORKSPACE_OUTPUT')
            for o in spec.outputs:
                p=outputs[o.output_id]
                if not p.is_file() or p.is_symlink() or p.stat().st_nlink!=1:row['issues'].append('PERF_OUTPUT_MISSING');continue
                if p.stat().st_size>policy.max_file_bytes:row['issues'].append('PERF_OUTPUT_SIZE');continue
                data=p.read_bytes()
                if not data:row['issues'].append('PERF_EMPTY_OUTPUT');continue
                row['outputs'][o.output_id]=publish(spec.job_id+'/out-'+o.output_id+('.mp4' if o.kind=='MP4' else '.bin'),data,'video' if o.kind=='MP4' else 'support')
                try:inspect_output(data,o,tools)
                except (ContractError,OSError) as exc:row['issues'].append(exc.code if isinstance(exc,ContractError) else 'PERF_OUTPUT_IO')
            row['issues']=sorted(set(row['issues']));row['complete_ns']=time.monotonic_ns()-origin
            return row
    with ThreadPoolExecutor(max_workers=policy.max_workers) as pool:jobs=list(pool.map(job,policy.jobs))
    after=capture_environment();verify_files(root,snapshot,exact=False)
    for p in producers:p.verify()
    raw=dict(schema_version='bie.qa.performance-execution/1',execution_id=execution_id,snapshot_digest=snapshot.content_digest,policy_digest=policy.content_digest,
        started_at=started_at,finished_at=time.time_ns()//1000000000,profile=PROFILE,environment_before=before,environment_after=after,
        collector_sha256=file_hash('collector.py'),launcher_sha256=file_hash('limit_exec.py'),probe_sha256=file_hash('memory_probe.py'),
        producers=[list(x) for x in policy.producer_bindings],queue_start_ns=qstart,queue_end_ns=max(j['complete_ns'] for j in jobs),jobs=jobs,memory_probe=probe,
        product_accepted=False,native_queue_executed=False)
    rid=publish('execution.json',canonical_bytes(raw))
    return PerformanceRequest(snapshot,tuple(sorted(evidence,key=lambda a:a.artifact_id)),rid)
