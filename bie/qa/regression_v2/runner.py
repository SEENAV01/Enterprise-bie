"""Generic before/after execution: registered trusted callbacks, private copies.

This is NOT a hostile-code sandbox. Callback source/module identity is pinned;
transitive imports and registry completeness remain operator obligations.
"""
from dataclasses import asdict
from pathlib import Path
import hashlib,multiprocessing,os,platform,signal,shutil,sys,tempfile,time,uuid
from ..release_v2.contracts import ContractError,canonical_bytes,digest,integer
from ..source_v2.codec import loads
from ..repair_audit_v2.io import verify_files,copy_snapshot
from ..repair_v2.worker import validator_digest
from .models import RegressionPolicy,Observation,binding

def obligations(baseline,candidate,policy):
    if type(policy) is not RegressionPolicy:raise ContractError('REG_POLICY_TYPE')
    a={r.artifact_id:r for r in baseline.artifacts};b={r.artifact_id:r for r in candidate.artifacts}
    for aid in policy.protected_artifact_ids:
        if aid not in a or aid not in b or a[aid]!=b[aid]:raise ContractError('REG_FIXTURE_OR_PROTECTED_CHANGED')
    for rule in policy.semantic+policy.visual+policy.game:
        if rule.artifact_id not in a or rule.artifact_id not in b:raise ContractError('REG_COMPARISON_ARTIFACT_MISSING')
    return a,b

def _child(conn,root,snapshot,policy,registry):
    try:
        os.setsid()
        import resource
        resource.setrlimit(resource.RLIMIT_CPU,(policy.phase_timeout_seconds,policy.phase_timeout_seconds+1))
        resource.setrlimit(resource.RLIMIT_AS,(1536*1024*1024,1536*1024*1024))
        resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024*1024,8*1024*1024))
        resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
        rows=[]
        for rule in policy.checks:
            got=registry[rule.check_id](root,snapshot,rule)
            if type(got) is not tuple or any(type(x) is not Observation for x in got):raise ContractError('REG_VALIDATOR_RETURN_TYPE')
            if tuple(x.case_id for x in got)!=rule.case_ids:raise ContractError('REG_CASE_COVERAGE')
            rows.append(dict(check_id=rule.check_id,validator_digest=rule.validator_digest,
                fixture_ids=rule.fixture_ids,cases=[asdict(x) for x in got]))
        raw=canonical_bytes(dict(checks=rows,error=''))
        if len(raw)>policy.max_evidence_bytes:raise ContractError('REG_WORKER_OUTPUT_LIMIT')
        conn.send_bytes(raw)
    except BaseException as e:
        try:conn.send_bytes(canonical_bytes(dict(checks=[],error=e.code if isinstance(e,ContractError) else 'REG_VALIDATOR_EXCEPTION')))
        except BaseException:pass
    finally:conn.close()

def _phase(phase,source,snapshot,policy,registry,parent,as_of):
    root=copy_snapshot(source,snapshot,parent)
    ctx=multiprocessing.get_context('fork');rd,wr=ctx.Pipe(duplex=False)
    p=ctx.Process(target=_child,args=(wr,str(root),snapshot,policy,registry))
    payload=dict(checks=[],error='REG_WORKER_NOT_STARTED');start=time.monotonic_ns();wall=time.time_ns();started=False;exitcode=None
    try:
        p.start();started=True;wr.close()
        if not rd.poll(policy.phase_timeout_seconds):payload['error']='REG_WORKER_TIMEOUT'
        else:
            try:
                got=loads(rd.recv_bytes(policy.max_evidence_bytes))
                if type(got) is not dict or set(got)!={'checks','error'} or type(got['error']) is not str:raise ContractError('REG_WORKER_PROTOCOL')
                payload=got
            except (EOFError,OSError,ContractError):payload=dict(checks=[],error='REG_WORKER_PROTOCOL')
        p.join(timeout=0.5);exitcode=p.exitcode
        if not payload['error'] and exitcode!=0:payload=dict(checks=[],error='REG_WORKER_EXIT')
    finally:
        if started:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            if p.is_alive():p.kill()
            p.join(timeout=2)
        rd.close();wr.close()
        try:verify_files(root,snapshot,exact=True)
        except (ContractError,OSError):payload=dict(checks=[],error='REG_VALIDATOR_MUTATED_COPY')
        shutil.rmtree(root,ignore_errors=True)
    return dict(phase=phase,snapshot_digest=snapshot.content_digest,execution_id='reg-'+uuid.uuid4().hex,
        executed_at=as_of,wall_started_ns=wall,wall_finished_ns=time.time_ns(),elapsed_ms=(time.monotonic_ns()-start)//1000000,
        worker_executed=started,process_exit=exitcode,error=payload['error'],checks=payload['checks'])

def collect(comparison_id,baseline,candidate,baseline_root,candidate_root,policy,*,registry,as_of):
    """Run both phases. The returned record is unsigned and needs verification."""
    integer(as_of,'as_of');obligations(baseline,candidate,policy)
    if os.name!='posix' or 'fork' not in multiprocessing.get_all_start_methods():raise ContractError('REG_WORKER_PLATFORM')
    a=Path(baseline_root).resolve();b=Path(candidate_root).resolve()
    if a==b or a.is_relative_to(b) or b.is_relative_to(a):raise ContractError('REG_ROOT_OVERLAP')
    if type(registry) is not dict or set(registry)!={r.check_id for r in policy.checks}:raise ContractError('REG_VALIDATOR_REGISTRY')
    for rule in policy.checks:
        if validator_digest(registry[rule.check_id])!=rule.validator_digest:raise ContractError('REG_VALIDATOR_IDENTITY')
    verify_files(baseline_root,baseline,exact=True);verify_files(candidate_root,candidate,exact=True)
    with tempfile.TemporaryDirectory(prefix='bie-regression-') as parent:
        before=_phase('baseline',baseline_root,baseline,policy,registry,parent,as_of)
        after=_phase('candidate',candidate_root,candidate,policy,registry,parent,as_of)
    verify_files(baseline_root,baseline,exact=True);verify_files(candidate_root,candidate,exact=True)
    env=dict(python=platform.python_version(),platform=platform.platform(),executable_sha256=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
        callback_scope='function and defining module pinned; transitive imports not certified',hostile_code_sandbox=False)
    return dict(schema_version='bie.qa.regression-execution/1',binding=binding(comparison_id,baseline,candidate,policy),
        evaluated_at=as_of,environment=env,environment_digest=digest(env),
        baseline=before,candidate=after,full_repository_regression_run=False,product_accepted=False)
