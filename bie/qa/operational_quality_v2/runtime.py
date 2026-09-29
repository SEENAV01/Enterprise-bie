"""HARD030 registered native-worker integration and explicit trusted diagnostics.

The trusted runner is *not* a sandbox. Isolation requests never fall back to it.
Native worker files must match a separately approved complete file inventory.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import os,sys,subprocess,time,signal,selectors,json,tempfile
from .common import *

@dataclass(frozen=True)
class Program:
    program_id:str
    argv:tuple[str,...]
    executable_sha256:str
    script_path:str
    script_sha256:str
    timeout_seconds:int=15
    max_log_bytes:int=1024*1024
    def __post_init__(self):
        token(self.program_id,'program');sha256(self.executable_sha256,'executable');sha256(self.script_sha256,'script')
        require(type(self.argv) is tuple and 2<=len(self.argv)<=128,'H7_ARGV')
        require(Path(self.argv[0]).is_absolute() and Path(self.script_path).is_absolute(),'H7_ABSOLUTE_PROGRAM')
        require(self.script_path in self.argv,'H7_SCRIPT_NOT_EXECUTED')
        for a in self.argv:require(type(a) is str and '\x00' not in a and len(a)<=4096,'H7_ARGUMENT')
        integer(self.timeout_seconds,'timeout',1,600);integer(self.max_log_bytes,'log',256,8*1024*1024)
    @property
    def content_digest(self):return digest(asdict(self))
    def verify(self):
        for p,expected in ((self.argv[0],self.executable_sha256),(self.script_path,self.script_sha256)):
            path=Path(p).resolve(strict=True)
            require(tool_identity(path)['sha256']==expected,'H7_PROGRAM_CHANGED')


def run_trusted(program,workspace,output,*,run_id=None,cancel=None):
    """Execute an explicitly trusted program; inputs read-only by contract/recheck.

    stdin is /dev/null, environment is fixed, complete bounded logs retained,
    process group is killed on timeout/cancel *and* after main process exits.
    This does not confine a hostile program; production callers use native_worker.
    """
    require(type(program) is Program,'H7_PROGRAM_TYPE');program.verify()
    workspace=real_dir(workspace);output=Path(output).absolute()
    require(not output.is_relative_to(workspace) and not workspace.is_relative_to(output),'H7_OUTPUT_INPUT_OVERLAP')
    output.mkdir(parents=True,exist_ok=False)
    before=inventory(workspace);execution_id=new_id();run_id=run_id or new_id();token(run_id,'run')
    if cancel is not None and cancel.is_set():raise ContractError('H7_CANCELLED_BEFORE_START')
    env={'PATH':'/usr/local/bin:/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC',
         'PYTHONHASHSEED':'0','PYTHONDONTWRITEBYTECODE':'1','SOURCE_DATE_EPOCH':'0','OAI_IS_JUPYTER_KERNEL':'0',
         'BIE_INPUT_ROOT':str(workspace),'BIE_OUTPUT_ROOT':str(output),'BIE_EXECUTION_ID':execution_id,'BIE_RUN_ID':run_id}
    start=time.monotonic_ns();wall=time.time_ns();reason=None;logs={'stdout':bytearray(),'stderr':bytearray()}
    p=subprocess.Popen(program.argv,cwd=workspace,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    sel=selectors.DefaultSelector()
    for name,stream in (('stdout',p.stdout),('stderr',p.stderr)):
        os.set_blocking(stream.fileno(),False);sel.register(stream,selectors.EVENT_READ,name)
    try:
        while sel.get_map():
            if cancel is not None and cancel.is_set():reason='CANCELLED';break
            if time.monotonic_ns()-start>program.timeout_seconds*1_000_000_000:reason='TIMEOUT';break
            for key,_ in sel.select(.02):
                data=os.read(key.fileobj.fileno(),65536)
                if not data:sel.unregister(key.fileobj);continue
                name=key.data
                if sum(map(len,logs.values()))+len(data)>program.max_log_bytes:reason='OUTPUT_LIMIT';break
                logs[name].extend(data)
            if reason:break
            if p.poll() is not None:
                # A descendant holding pipes must not keep a completed job alive.
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
        if reason is None:
            try:code=p.wait(timeout=max(.001,program.timeout_seconds-(time.monotonic_ns()-start)/1e9))
            except subprocess.TimeoutExpired:reason='TIMEOUT'
    finally:
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        p.wait(timeout=5);sel.close();p.stdout.close();p.stderr.close()
    end=time.monotonic_ns()
    program.verify();after=inventory(workspace)
    if after!=before:reason='INPUT_CHANGED'
    if reason is None and p.returncode!=0:reason='NONZERO_EXIT'
    rows=inventory(output)
    return dict(schema_version='bie.qa.h7-process/1',execution_id=execution_id,run_id=run_id,program_digest=program.content_digest,
        input_digest=digest(before),inputs=before,outputs=rows,output_digest=digest(rows),started_ns=start,finished_ns=end,
        started_wall_ns=wall,finished_wall_ns=time.time_ns(),exit_code=p.returncode,error=reason,
        stdout=bytes(logs['stdout']).decode('utf-8','replace'),stderr=bytes(logs['stderr']).decode('utf-8','replace'),
        stdout_sha256=identity(bytes(logs['stdout'])),stderr_sha256=identity(bytes(logs['stderr'])),
        kind='TRUSTED_DIAGNOSTIC_PROCESS',process_group_cleanup_attempted=True,kernel_isolated=False,product_accepted=False)

@dataclass(frozen=True)
class NativeWorkerProfile:
    checkout_rows:tuple[dict,...]
    worker_sha256:str
    launcher_sha256:str
    timeout_seconds:int=30
    def __post_init__(self):
        sha256(self.worker_sha256,'worker');sha256(self.launcher_sha256,'launcher')
        require(type(self.checkout_rows) is tuple and bool(self.checkout_rows),'H7_NATIVE_INVENTORY')
        require(len({r['path'] for r in self.checkout_rows})==len(self.checkout_rows),'H7_NATIVE_DUPLICATE')
        integer(self.timeout_seconds,'timeout',1,595)
    @property
    def content_digest(self):return digest(asdict(self))

def validate_kernel_proof(proof,profile):
    require(type(proof) is dict and proof.get('schema_version')=='bie.linux-worker-proof.v1','H7_NATIVE_PROOF_SCHEMA')
    for k in ('kernel_enforced','read_only_workspace_except_declared','capabilities_dropped','no_new_privileges'):
        require(proof.get(k) is True,'H7_NATIVE_CONTROL_MISSING')
    require(proof.get('launcher_sha256')==profile.launcher_sha256,'H7_NATIVE_LAUNCHER_BINDING')
    require(proof.get('private_network')=='LOOPBACK_ONLY_NO_HOST_ROUTE','H7_NATIVE_NETWORK')
    require(set(proof.get('namespaces',{}))=={'net','mnt','pid','user'},'H7_NATIVE_NAMESPACE_CENSUS')
    require({'mount','setns','ptrace','process_vm_writev'}<=set(proof.get('seccomp_denied_syscalls',[])),'H7_NATIVE_FILTER')
    require(proof.get('accepted') is False,'H7_NATIVE_PROMOTED')
    return True

def native_worker(checkout,profile,command,workspace,*,writable=('outputs',),output):
    """Calls the existing canonical worker from a fully pinned private checkout.

    Caller must provision the approved checkout and dependencies. Missing kernel
    support, engine bytes or proof blocks; no diagnostic callback is substituted.
    """
    require(type(profile) is NativeWorkerProfile,'H7_NATIVE_PROFILE')
    require(inventory(checkout)==list(profile.checkout_rows),'H7_NATIVE_CHECKOUT_CHANGED')
    for name,expected in (('linux_worker.py',profile.worker_sha256),('namespace_launcher.py',profile.launcher_sha256)):
        require(identity(regular_bytes(checkout,'bie/compiler/'+name))==expected,'H7_NATIVE_SOURCE_BINDING')
    for p in writable:
        safe_relative_path(p);require(p=='outputs' or p.startswith('outputs/'),'H7_NATIVE_WRITABLE_SCOPE')
    require(type(command) is tuple and command and Path(command[0]).is_absolute(),'H7_NATIVE_COMMAND')
    payload=dict(checkout=str(real_dir(checkout)),workspace=str(real_dir(workspace)),command=command,writable=writable,timeout=profile.timeout_seconds)
    worker=Path(__file__).with_name('native_worker_entry.py')
    with tempfile.TemporaryDirectory(prefix='bie-h7-native-') as d:
        inp=Path(d)/'input';inp.mkdir();(inp/'request.json').write_bytes(canonical_bytes(payload))
        prog=Program('native-worker-entry',(str(Path(sys.executable).resolve()),'-I','-B',str(worker)),identity(Path(sys.executable).resolve().read_bytes()),str(worker),identity(worker.read_bytes()),profile.timeout_seconds+5)
        rec=run_trusted(prog,inp,output)
    require(inventory(checkout)==list(profile.checkout_rows),'H7_NATIVE_CHECKOUT_CHANGED')
    if rec['error']:return dict(status='BLOCKED',process=rec,native_executed=False,product_accepted=False)
    result=strict_object(regular_bytes(output,'native.json'))
    if result.get('error'):return dict(status='BLOCKED',process=rec,native_executed=False,error=result['error'],product_accepted=False)
    validate_kernel_proof(result['proof'],profile)
    require(result['outcome']=='SUCCEEDED' and result['exit_code']==0,'H7_NATIVE_EXECUTION_FAILED')
    return dict(status='REVIEW_REQUIRED',process=rec,native_executed=True,proof=result['proof'],product_accepted=False)
