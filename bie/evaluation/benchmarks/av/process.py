"""H2-002: POSIX streamed subprocess IO, quotas, monotonic deadline, group kill.

Only evaluator-controlled argv are permitted. Child CPU/memory/network policy
and escaped descendants require deployment OS containment; not claimed here.
"""
from __future__ import annotations
from pathlib import Path
import hashlib, os, selectors, shutil, signal, subprocess, time
from ..models import BenchmarkError

class Deadline:
    def __init__(self, seconds):
        from .custody import finite
        finite(seconds,0.001,86400);self.end=time.monotonic()+seconds
    def remaining(self):
        r=self.end-time.monotonic()
        if r<=0: raise BenchmarkError('AV_DEADLINE')
        return r

def executable(name):
    p=shutil.which(name)
    if not p: raise BenchmarkError('AV_TOOL_UNAVAILABLE',name)
    return str(Path(p).resolve())

def _kill(p):
    try: os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError: pass
    p.wait(timeout=5)

def stream(argv, cwd, deadline, consume, *, max_stdout, max_stderr=262144):
    from .custody import integer
    integer(max_stdout,0,2**50);integer(max_stderr,0,2**50)
    if type(deadline) is not Deadline or not callable(consume):raise BenchmarkError('INVALID_PROCESS_BOUNDARY')
    if os.name!='posix': raise BenchmarkError('AV_PLATFORM_UNVERIFIED')
    if type(argv) is not list or not argv or any(type(a) is not str or '\x00' in a for a in argv):
        raise BenchmarkError('INVALID_TOOL_ARGV')
    if not Path(argv[0]).is_absolute(): raise BenchmarkError('TOOL_PATH_NOT_PINNED')
    deadline.remaining();out_hash=hashlib.sha256();err_hash=hashlib.sha256();n=0;ne=0
    env={'PATH':'/usr/bin:/bin','HOME':str(cwd),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'}
    p=subprocess.Popen(argv,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,shell=False,start_new_session=True,bufsize=0)
    sel=selectors.DefaultSelector()
    try:
        for f in (p.stdout,p.stderr):
            os.set_blocking(f.fileno(),False);sel.register(f,selectors.EVENT_READ)
        while sel.get_map():
            for key,_ in sel.select(min(deadline.remaining(),0.25)):
                b=os.read(key.fileobj.fileno(),65536)
                if not b: sel.unregister(key.fileobj);continue
                if key.fileobj is p.stdout:
                    n+=len(b)
                    if n>max_stdout: raise BenchmarkError('AV_STDOUT_LIMIT')
                    out_hash.update(b);consume(b)
                else:
                    ne+=len(b)
                    if ne>max_stderr: raise BenchmarkError('AV_STDERR_LIMIT')
                    err_hash.update(b)
        try: rc=p.wait(timeout=deadline.remaining())
        except subprocess.TimeoutExpired as e: raise BenchmarkError('AV_DEADLINE') from e
        if rc!=0 or ne: raise BenchmarkError('AV_TOOL_FAILED')
        return {'argv':argv,'stdout_bytes':n,'stdout_sha256':out_hash.hexdigest(),
                'stderr_bytes':ne,'stderr_sha256':err_hash.hexdigest(),'exit_code':rc}
    finally:
        sel.close()
        if p.poll() is None: _kill(p)
        else:
            # A child may exit while descendants remain in its process group.
            try: os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError: pass
        p.stdout.close();p.stderr.close()

def capture(argv,cwd,deadline,limit=2_000_000):
    parts=[];receipt=stream(argv,cwd,deadline,parts.append,max_stdout=limit)
    return b''.join(parts),receipt

class Lines:
    """Bounded line framer over arbitrary binary reads."""
    def __init__(self, consume, max_line=8192):
        from .custody import integer
        integer(max_line,1,1_000_000)
        if not callable(consume):raise BenchmarkError('INVALID_LINE_CONSUMER')
        self.pending=bytearray();self.consume=consume;self.max_line=max_line
    def feed(self,b):
        self.pending.extend(b)
        while (i:=self.pending.find(b'\n'))>=0:
            if i>self.max_line: raise BenchmarkError('AV_TIMING_LINE_LIMIT')
            line=bytes(self.pending[:i]);del self.pending[:i+1]
            if line:self.consume(line.decode('utf-8',errors='strict'))
        if len(self.pending)>self.max_line: raise BenchmarkError('AV_TIMING_LINE_LIMIT')
    def finish(self):
        if self.pending:
            self.consume(bytes(self.pending).decode('utf-8',errors='strict'));self.pending.clear()
