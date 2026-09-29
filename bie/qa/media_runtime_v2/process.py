"""Deadline-bound streams; no shell, no request-supplied executables.

Trusted registered tools only. Does not claim filesystem/network isolation for
arbitrary generated programs. All process groups are killed/reaped on error.
"""
from __future__ import annotations
from contextlib import contextmanager
import os,selectors,signal,subprocess,time,threading
from .common import require, ContractError, integer

@contextmanager
def pipe(argv, *, timeout=120, stderr_limit=65536, cwd=None, allow_nonzero=False):
    integer(timeout,'timeout',1,3600)
    p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                       start_new_session=True,bufsize=0,cwd=cwd,env={'PATH':'/usr/bin:/bin','LC_ALL':'C','LANG':'C','HOME':'/nonexistent'})
    err=bytearray();overflow=threading.Event()
    def drain():
        while b:=p.stderr.read(4096):
            if len(err)+len(b)>stderr_limit:overflow.set()
            if len(err)<stderr_limit:err.extend(b[:stderr_limit-len(err)])
    t=threading.Thread(target=drain,daemon=True);t.start()
    sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
    deadline=time.monotonic()+timeout;buffer=bytearray();eof=False
    def read(size):
        nonlocal eof
        require(type(size)is int and 0<=size<=128*1024**2,'H5_PIPE_READ_BUDGET')
        while len(buffer)<size and not eof:
            require(not overflow.is_set(),'H5_PROCESS_LOG_BUDGET')
            left=deadline-time.monotonic()
            if left<=0:raise ContractError('H5_PROCESS_TIMEOUT')
            if not sel.select(min(left,0.5)):continue
            b=os.read(p.stdout.fileno(),min(1048576,max(1,size-len(buffer))))
            if not b:eof=True;break
            buffer.extend(b)
        data=bytes(buffer[:size]);del buffer[:size];return data
    def line(maximum=4096):
        out=bytearray()
        while True:
            b=read(1)
            if not b or b==b'\n':return bytes(out)
            out+=b
            require(len(out)<=maximum,'H5_PROCESS_LINE_BUDGET')
    handle={'pid':p.pid,'read':read,'line':line,'stderr':err,'process':p}
    try:
        yield handle
        require(not buffer and not read(1),'H5_PROCESS_UNCONSUMED_OUTPUT')
        left=deadline-time.monotonic();require(left>0,'H5_PROCESS_TIMEOUT')
        try:rc=p.wait(timeout=left)
        except subprocess.TimeoutExpired as exc:raise ContractError('H5_PROCESS_TIMEOUT') from exc
        t.join(timeout=2)
        require(not overflow.is_set(),'H5_PROCESS_LOG_BUDGET')
        handle['exit_code']=rc
        if not allow_nonzero:require(rc==0,'H5_PROCESS_FAILED')
    finally:
        if p.poll() is None:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            p.wait()
        # Kill leftover children in the same group, even after leader exited.
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        sel.close();p.stdout.close();p.stderr.close();t.join(timeout=1)


def capture(argv, *, timeout=60, output_limit=1024**2):
    with pipe(argv,timeout=timeout) as h:
        data=h['read'](output_limit+1)
        require(len(data)<=output_limit,'H5_PROCESS_OUTPUT_BUDGET')
    return data
