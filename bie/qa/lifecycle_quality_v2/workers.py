"""Bounded operator-registered callbacks. Process separation, NOT hostile-code isolation."""
from __future__ import annotations
from dataclasses import dataclass
import multiprocessing as mp,os,signal,time,hashlib
from .common import *

@dataclass(frozen=True)
class Callback:
    callback_id:str
    identity:str
    function:object
    def __post_init__(self):
        token(self.callback_id,'callback');sha256(self.identity,'callback identity')
        require(validator_digest(self.function)==self.identity,'H6_CALLBACK_IDENTITY')
    def verify(self):
        require(validator_digest(self.function)==self.identity,'H6_CALLBACK_CHANGED')

def _child(conn,fn,payload,seconds,max_bytes):
    try:
        os.setsid()
        import resource
        resource.setrlimit(resource.RLIMIT_CPU,(seconds,seconds+1))
        resource.setrlimit(resource.RLIMIT_FSIZE,(max_bytes,max_bytes))
        resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
        value=fn(payload)
        require(type(value) is bytes and len(value)<=max_bytes,'H6_WORKER_OUTPUT_LIMIT')
        conn.send_bytes(b'0'+value)
    except BaseException as exc:
        try:conn.send_bytes(b'1'+(exc.code if isinstance(exc,ContractError) else 'H6_CALLBACK_FAILED').encode())
        except BaseException:pass
    finally:conn.close()

def invoke(callback,payload,*,timeout=10,max_bytes=2*1024*1024,cancel=None):
    require(type(callback) is Callback and type(payload) is bytes,'H6_WORKER_INPUT')
    integer(timeout,'timeout',1,60);integer(max_bytes,'output bytes',1,8*1024*1024)
    require(os.name=='posix' and 'fork' in mp.get_all_start_methods(),'H6_WORKER_PLATFORM')
    callback.verify()
    require(cancel is None or not cancel.is_set(),'H6_CANCELLED')
    ctx=mp.get_context('fork');rd,wr=ctx.Pipe(duplex=False)
    p=ctx.Process(target=_child,args=(wr,callback.function,payload,timeout,max_bytes))
    start=time.monotonic();p.start();wr.close();wire=None;error=None
    try:
        while time.monotonic()-start<timeout:
            if cancel is not None and cancel.is_set():error='H6_CANCELLED';break
            if rd.poll(.02):
                try:wire=rd.recv_bytes(max_bytes+256)
                except (OSError,EOFError):error='H6_WORKER_CHANNEL'
                break
            if not p.is_alive():error='H6_WORKER_EXIT';break
        if wire is None and error is None:error='H6_WORKER_TIMEOUT'
        if wire is not None:
            if wire[:1]==b'1':error=wire[1:].decode('utf-8','replace')
            elif wire[:1]!=b'0':error='H6_WORKER_PROTOCOL'
        p.join(.2)
        if wire is not None and p.exitcode not in (0,None):error='H6_WORKER_EXIT'
    finally:
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        if p.is_alive():p.kill()
        p.join(2);rd.close()
    callback.verify()
    receipt=dict(callback_id=callback.callback_id,callback_digest=callback.identity,pid=p.pid,
       elapsed_ms=int((time.monotonic()-start)*1000),error=error,worker_executed=True,
       input_sha256=hashlib.sha256(payload).hexdigest(),output_sha256=hashlib.sha256(wire[1:]).hexdigest() if wire and not error else None,
       process_group_termination_attempted=True,hostile_code_sandbox=False)
    return (wire[1:] if wire and not error else None),receipt
