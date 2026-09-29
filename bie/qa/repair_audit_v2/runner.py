"""Actual bounded before/after execution on disposable private copies.

Validators are operator-registered TOP-LEVEL Python functions, pinned by source.
No callback name or shell command is read from request JSON. This worker is NOT
an adversarial code sandbox. Its import dependencies remain operator-governed.
"""
from dataclasses import asdict
from pathlib import Path
import hashlib,multiprocessing,os,platform,signal,shutil,sys,tempfile,time,uuid
from ..release_v2.contracts import ContractError,canonical_bytes,digest,integer
from ..source_v2.codec import loads
from ..repair_v2.worker import validator_digest
from .models import AuditPolicy,Observation,candidate_for,run_binding
from .regression import validate_obligations
from .io import verify_files,copy_snapshot

def _child(conn,root,snapshot,repair_policy,audit_policy,registry):
    try:
        os.setsid()
        import resource
        limit=audit_policy.phase_timeout_seconds
        resource.setrlimit(resource.RLIMIT_CPU,(limit,limit+1))
        resource.setrlimit(resource.RLIMIT_AS,(1536*1024*1024,1536*1024*1024))
        resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024*1024,8*1024*1024))
        resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
        rows=[]
        for rule in audit_policy.checks:
            items=registry[rule.check_id](str(root),snapshot,repair_policy,rule)
            if type(items) is not tuple or any(type(x) is not Observation for x in items):
                raise ContractError('AUDIT_VALIDATOR_RETURN_TYPE')
            if tuple(x.case_id for x in items)!=rule.case_ids:raise ContractError('AUDIT_CASE_COVERAGE')
            rows.append(dict(check_id=rule.check_id,validator_digest=rule.validator_digest,
                fixture_ids=rule.fixture_ids,cases=[asdict(x) for x in items]))
        data=canonical_bytes(dict(checks=rows,error=''))
        if len(data)>audit_policy.max_evidence_bytes:raise ContractError('AUDIT_WORKER_OUTPUT_LIMIT')
        conn.send_bytes(data)
    except BaseException as exc:
        try:conn.send_bytes(canonical_bytes(dict(checks=[],error=exc.code if isinstance(exc,ContractError) else 'AUDIT_VALIDATOR_EXCEPTION')))
        except BaseException:pass
    finally:conn.close()

def _phase(phase,source,snapshot,repair_policy,audit_policy,registry,parent,as_of):
    root=copy_snapshot(source,snapshot,parent)
    ctx=multiprocessing.get_context('fork');reader,writer=ctx.Pipe(duplex=False)
    process=ctx.Process(target=_child,args=(writer,str(root),snapshot,repair_policy,audit_policy,registry))
    wall=time.time_ns();start=time.monotonic_ns();payload=dict(checks=[],error='AUDIT_WORKER_NOT_STARTED');started=False
    try:
        process.start();started=True;writer.close()
        if not reader.poll(audit_policy.phase_timeout_seconds):payload['error']='AUDIT_WORKER_TIMEOUT'
        else:
            try:
                data=loads(reader.recv_bytes(audit_policy.max_evidence_bytes))
                if type(data) is not dict or set(data)!={'checks','error'} or type(data['error']) is not str:
                    raise ContractError('AUDIT_WORKER_PROTOCOL')
                payload=data
            except (OSError,EOFError,ContractError):payload=dict(checks=[],error='AUDIT_WORKER_PROTOCOL')
        process.join(timeout=0.2)
        if process.exitcode not in (0,None) and not payload['error']:payload['error']='AUDIT_WORKER_EXIT'
    finally:
        if started:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            if process.is_alive():process.kill()
            process.join(timeout=2)
        reader.close();writer.close()
        try:verify_files(root,snapshot,exact=True)
        except (ContractError,OSError):payload=dict(checks=[],error='AUDIT_VALIDATOR_MUTATED_COPY')
        shutil.rmtree(root,ignore_errors=True)
    return dict(phase=phase,snapshot_digest=snapshot.content_digest,execution_id='execution-'+uuid.uuid4().hex,
        executed_at=as_of,wall_started_ns=wall,wall_finished_ns=time.time_ns(),elapsed_ms=(time.monotonic_ns()-start)//1000000,
        worker_executed=started,error=payload['error'],checks=payload['checks'])

def collect_regression(snapshot,proposal,original_root,candidate_root,repair_policy,audit_policy,*,registry,as_of):
    """Execute both phases. Returned records are unsigned; audit before trusting them."""
    integer(as_of,'as_of')
    if type(audit_policy) is not AuditPolicy:raise ContractError('AUDIT_POLICY_TYPE')
    validate_obligations(snapshot,proposal,repair_policy,audit_policy)
    if os.name!='posix' or 'fork' not in multiprocessing.get_all_start_methods():raise ContractError('AUDIT_WORKER_PLATFORM')
    if type(registry) is not dict or set(registry)!={r.check_id for r in audit_policy.checks}:
        raise ContractError('AUDIT_VALIDATOR_REGISTRY')
    for rule in audit_policy.checks:
        if validator_digest(registry[rule.check_id])!=rule.validator_digest:
            raise ContractError('AUDIT_VALIDATOR_IDENTITY')
    original=Path(original_root);candidate=Path(candidate_root)
    if original.resolve()==candidate.resolve() or original.resolve().is_relative_to(candidate.resolve()) or candidate.resolve().is_relative_to(original.resolve()):
        raise ContractError('AUDIT_ROOT_OVERLAP')
    after=candidate_for(snapshot,proposal)
    verify_files(original,snapshot);verify_files(candidate,after,exact=True)
    environment=dict(python_version=platform.python_version(),platform=platform.platform(),
        executable_sha256=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
        callback_scope='source/module pinned; transitive import closure not independently established',
        observation_clock='operator supplied as_of; actual wall nanoseconds separately recorded')
    with tempfile.TemporaryDirectory(prefix='bie-repair-regression-') as parent:
        before_run=_phase('baseline',original,snapshot,repair_policy,audit_policy,registry,parent,as_of)
        after_run=_phase('candidate',candidate,after,repair_policy,audit_policy,registry,parent,as_of)
    # A validator never receives these originals; still recheck actual input bytes.
    verify_files(original,snapshot);verify_files(candidate,after,exact=True)
    fixture_ids={x for r in audit_policy.checks for x in r.fixture_ids}
    return dict(schema_version='bie.qa.repair-regression/1',binding=run_binding(snapshot,proposal,repair_policy,audit_policy),
        evaluated_at=as_of,executor_scope='LOCAL_TRUSTED_VALIDATORS_PRIVATE_COPIES',environment=environment,
        environment_digest=digest(environment),fixture_manifest=[asdict(a) for a in sorted(snapshot.artifacts,key=lambda a:a.artifact_id) if a.artifact_id in fixture_ids],
        baseline=before_run,candidate=after_run,product_accepted=False,full_repository_regression_run=False)
