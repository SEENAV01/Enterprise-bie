"""Hard-time-bounded POSIX worker for OPERATOR-REGISTERED trusted validators.

No import target, shell command or executable comes from repair input. This is
process separation/resource bounding, NOT a sandbox for hostile generated code.
Production network/filesystem isolation remains an external deployment obligation.
"""
from __future__ import annotations
from dataclasses import asdict
import multiprocessing,os,signal,time
from ..release_v2.contracts import ContractError,canonical_bytes
from ..source_v2.codec import loads
from .models import CheckOutcome
from .codec import decode

def validator_digest(fn):
    """Pin trusted Python callback source/module identity, not its transitive imports."""
    import inspect,hashlib,platform,types
    from pathlib import Path
    from ..release_v2.contracts import digest
    if type(fn) is not types.FunctionType or fn.__closure__ is not None:
        raise ContractError('REPAIR_VALIDATOR_MUST_BE_TOP_LEVEL_FUNCTION')
    try:
        path=inspect.getsourcefile(fn)
        if not path:raise OSError('no source')
        data=Path(path).read_bytes();source=inspect.getsource(fn)
    except (OSError,TypeError) as exc:raise ContractError('REPAIR_VALIDATOR_SOURCE_UNAVAILABLE') from exc
    return digest(dict(module=fn.__module__,qualified_name=fn.__qualname__,
        module_sha256=hashlib.sha256(data).hexdigest(),function_source=source,
        python=platform.python_version()))

def validate_registry(policy,required,registry):
    if type(registry) is not dict or not set(required)<=set(registry):raise ContractError('REPAIR_REQUIRED_CHECK_UNAVAILABLE')
    nodes={n.check_id:n for n in policy.checks}
    for name in required:
        if validator_digest(registry[name])!=nodes[name].validator_digest:
            raise ContractError('REPAIR_VALIDATOR_IDENTITY_MISMATCH',name)

def _child(conn,root,snapshot,policy,required,registry):
    try:
        os.setsid()
        import resource
        resource.setrlimit(resource.RLIMIT_CPU,(policy.worker_timeout_seconds,policy.worker_timeout_seconds+1))
        resource.setrlimit(resource.RLIMIT_AS,(1536*1024*1024,1536*1024*1024))
        resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024*1024,8*1024*1024))
        resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
        outcomes=[]
        for name in required:
            result=registry[name](root,snapshot,policy)
            if type(result) is not CheckOutcome:raise ContractError('REPAIR_WORKER_RETURN_TYPE')
            outcomes.append(asdict(result))
        conn.send_bytes(canonical_bytes(dict(outcomes=outcomes,error='')))
    except BaseException as exc:
        try:conn.send_bytes(canonical_bytes(dict(outcomes=[],error=exc.code if isinstance(exc,ContractError) else 'REPAIR_CHECK_EXCEPTION')))
        except BaseException:pass
    finally:conn.close()

def run_checks(root,snapshot,policy,required,registry):
    if os.name!='posix' or 'fork' not in multiprocessing.get_all_start_methods():raise ContractError('REPAIR_WORKER_PLATFORM_UNSUPPORTED')
    if type(registry) is not dict or any(type(k) is not str or not callable(v) for k,v in registry.items()):raise ContractError('REPAIR_CHECK_REGISTRY')
    if not set(required)<=set(registry):raise ContractError('REPAIR_REQUIRED_CHECK_UNAVAILABLE')
    validate_registry(policy,required,registry)
    ctx=multiprocessing.get_context('fork');reader,writer=ctx.Pipe(duplex=False)
    p=ctx.Process(target=_child,args=(writer,str(root),snapshot,policy,required,registry))
    started=time.monotonic();p.start();writer.close();error='';outcomes=()
    try:
        if not reader.poll(policy.worker_timeout_seconds):error='REPAIR_CHECK_TIMEOUT'
        else:
            try:wire=reader.recv_bytes(2*1024*1024);data=loads(wire)
            except (OSError,EOFError,ContractError):data=dict(outcomes=[],error='REPAIR_WORKER_CHANNEL')
            if type(data) is not dict or set(data)!={'outcomes','error'} or type(data['error']) is not str:error='REPAIR_WORKER_PROTOCOL'
            elif data['error']:error=data['error']
            else:
                outcomes=decode(data['outcomes'],tuple[CheckOutcome,...])
                if tuple(r.check_id for r in outcomes)!=required:error='REPAIR_CHECK_COVERAGE'
                elif any((r.candidate_digest,r.policy_digest)!=(snapshot.content_digest,policy.content_digest) for r in outcomes):error='REPAIR_CHECK_BINDING'
        p.join(timeout=0.2)
        if not error and p.exitcode not in (0,None):error='REPAIR_WORKER_EXIT'
    finally:
        # Kill the worker's whole process group, including any lingering children.
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        if p.is_alive():p.kill()
        p.join(timeout=2);reader.close()
    return dict(outcomes=outcomes,error=error,elapsed_ms=int((time.monotonic()-started)*1000),worker_executed=True,hostile_code_sandbox=False)
