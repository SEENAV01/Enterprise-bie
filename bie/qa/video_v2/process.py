"""Bounded POSIX subprocess capture; not a hostile-code execution sandbox.

Callers use operator-installed tools and fixed argv construction. Candidate receipt
commands are NEVER executed. Timeout and output limits terminate the process group.
"""
import os,selectors,signal,subprocess,time
from dataclasses import dataclass
from pathlib import Path
import hashlib,shutil
from ..release_v2.contracts import ContractError,integer

@dataclass(frozen=True,slots=True)
class ProcessResult:
    returncode:int
    stdout:bytes
    stderr:bytes

def run_bounded(argv,*,timeout=30,max_stdout=67108864,max_stderr=1048576,cwd=None):
    if os.name!='posix':raise ContractError('VIDEO_POSIX_WORKER_REQUIRED')
    if type(argv) not in (tuple,list) or not argv or any(type(x) is not str or '\0' in x for x in argv) or not Path(argv[0]).is_absolute():raise ContractError('VIDEO_OPERATOR_COMMAND_REQUIRED')
    integer(timeout,'timeout',1,120);integer(max_stdout,'stdout_limit',1,268435456);integer(max_stderr,'stderr_limit',1,4194304)
    try:p=subprocess.Popen(argv,cwd=cwd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','LC_ALL':'C'})
    except OSError as exc:raise ContractError('VIDEO_TOOL_START_FAILED') from exc
    out,err=bytearray(),bytearray();sel=selectors.DefaultSelector();deadline=time.monotonic()+timeout
    try:
        for pipe,name in ((p.stdout,'stdout'),(p.stderr,'stderr')):
            os.set_blocking(pipe.fileno(),False);sel.register(pipe,selectors.EVENT_READ,name)
        while sel.get_map():
            remaining=deadline-time.monotonic()
            if remaining<=0:raise ContractError('VIDEO_TOOL_TIMEOUT')
            for key,_ in sel.select(min(remaining,0.05)):
                data=os.read(key.fileobj.fileno(),65536)
                if not data:sel.unregister(key.fileobj);continue
                dst=out if key.data=='stdout' else err;dst.extend(data)
                if len(dst)>(max_stdout if key.data=='stdout' else max_stderr):raise ContractError('VIDEO_TOOL_OUTPUT_LIMIT')
        remaining=deadline-time.monotonic()
        if remaining<=0:raise ContractError('VIDEO_TOOL_TIMEOUT')
        try:rc=p.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:raise ContractError('VIDEO_TOOL_TIMEOUT') from exc
        return ProcessResult(rc,bytes(out),bytes(err))
    finally:
        # Kill even an exited leader's descendants; local worker must be private.
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        p.wait();sel.close();p.stdout.close();p.stderr.close()

@dataclass(frozen=True,slots=True)
class MediaTools:
    ffmpeg:str
    ffprobe:str
    def __post_init__(self):
        for n in ('ffmpeg','ffprobe'):
            p=Path(getattr(self,n))
            if not p.is_absolute() or not p.is_file() or not os.access(p,os.X_OK):raise ContractError('VIDEO_TOOL_UNAVAILABLE',n)
    @classmethod
    def discover(cls):
        f=shutil.which('ffmpeg');p=shutil.which('ffprobe')
        if not f or not p:raise ContractError('VIDEO_TOOL_UNAVAILABLE')
        return cls(str(Path(f).resolve()),str(Path(p).resolve()))
    def identity(self):
        out={}
        for n in ('ffmpeg','ffprobe'):
            path=Path(getattr(self,n));r=run_bounded([str(path),'-version'],timeout=5,max_stdout=65536)
            if r.returncode:raise ContractError('VIDEO_TOOL_VERSION_FAILED')
            out[n]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'version':r.stdout.decode(errors='replace').splitlines()[0]}
        return out
