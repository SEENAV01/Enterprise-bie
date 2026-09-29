"""Case-by-case comparison: coverage and regressions cannot be averaged away."""
from dataclasses import asdict
from ..release_v2.contracts import ContractError,digest,integer,sha256,token
from ..repair_v2.codec import decode
from ..repair_v2.planner import check_closure
from .models import Observation,run_binding,candidate_for
from .io import fields,equal

def validate_obligations(snapshot,proposal,repair_policy,audit_policy):
    required,_=check_closure(repair_policy,proposal.owner)
    equal(tuple(x.check_id for x in audit_policy.checks),required,'AUDIT_POLICY_CHECK_COVERAGE')
    equal(set_as_tuple(t.failure_id for t in audit_policy.targets),tuple(sorted(proposal.target_failure_ids)),'AUDIT_TARGET_FAILURE_COVERAGE')
    artifacts={a.artifact_id:a for a in snapshot.artifacts}
    if not set(audit_policy.protected_artifact_ids)<=set(artifacts):raise ContractError('AUDIT_PROTECTED_UNKNOWN')
    protected_paths={artifacts[k].path for k in audit_policy.protected_artifact_ids}
    if protected_paths & {r.path for r in proposal.replacements}:raise ContractError('AUDIT_PROTECTED_MUTATION')
    # Fixture bytes are the same on both sides; no repaired test/expected answer.
    return required

def set_as_tuple(values):return tuple(sorted(set(values)))

TOP_FIELDS=('schema_version binding evaluated_at executor_scope environment environment_digest fixture_manifest '
    'baseline candidate product_accepted full_repository_regression_run').split()
RUN_FIELDS=('phase snapshot_digest execution_id executed_at wall_started_ns wall_finished_ns elapsed_ms '
    'worker_executed error checks').split()
CHECK_FIELDS=('check_id validator_digest fixture_ids cases').split()

def inspect_regression(obj,snapshot,proposal,repair_policy,audit_policy,*,as_of):
    validate_obligations(snapshot,proposal,repair_policy,audit_policy)
    fields(obj,TOP_FIELDS,'AUDIT_REGRESSION_SCHEMA')
    equal(obj['schema_version'],'bie.qa.repair-regression/1','AUDIT_REGRESSION_VERSION')
    equal(obj['binding'],run_binding(snapshot,proposal,repair_policy,audit_policy),'AUDIT_REGRESSION_BINDING')
    equal(obj['executor_scope'],'LOCAL_TRUSTED_VALIDATORS_PRIVATE_COPIES','AUDIT_REGRESSION_EXECUTOR')
    equal(obj['product_accepted'],False,'AUDIT_REGRESSION_SCOPE')
    equal(obj['full_repository_regression_run'],False,'AUDIT_REGRESSION_SCOPE')
    integer(obj['evaluated_at'],'evaluated_at')
    if not 0<=as_of-obj['evaluated_at']<=audit_policy.max_receipt_age_seconds:raise ContractError('AUDIT_REGRESSION_STALE')
    if type(obj['environment']) is not dict or not obj['environment']:raise ContractError('AUDIT_ENVIRONMENT_RECORD')
    sha256(obj['environment_digest'],'environment_digest')
    equal(obj['environment_digest'],digest(obj['environment']),'AUDIT_ENVIRONMENT_DIGEST')
    fixture_ids={x for rule in audit_policy.checks for x in rule.fixture_ids}
    fixture_manifest=[asdict(a) for a in sorted(snapshot.artifacts,key=lambda a:a.artifact_id) if a.artifact_id in fixture_ids]
    equal(obj['fixture_manifest'],fixture_manifest,'AUDIT_FIXTURE_BYTES')
    runs={};identities=[]
    for phase,snap in (('baseline',snapshot),('candidate',candidate_for(snapshot,proposal))):
        run=obj[phase];fields(run,RUN_FIELDS,'AUDIT_RUN_SCHEMA')
        equal(run['phase'],phase,'AUDIT_RUN_PHASE');equal(run['snapshot_digest'],snap.content_digest,'AUDIT_RUN_SNAPSHOT')
        token(run['execution_id'],'execution_id');identities.append(run['execution_id'])
        integer(run['executed_at'],'executed_at')
        if not 0<=as_of-run['executed_at']<=audit_policy.max_receipt_age_seconds:raise ContractError('AUDIT_RUN_STALE')
        integer(run['wall_started_ns'],'wall_started_ns',1,2**63-1)
        integer(run['wall_finished_ns'],'wall_finished_ns',run['wall_started_ns'],2**63-1)
        integer(run['elapsed_ms'],'elapsed_ms',0,(audit_policy.phase_timeout_seconds+5)*1000)
        equal(run['worker_executed'],True,'AUDIT_REGRESSION_NOT_EXECUTED')
        if type(run['error']) is not str or run['error']:raise ContractError('AUDIT_REGRESSION_WORKER_ERROR')
        if type(run['checks']) is not list or len(run['checks'])!=len(audit_policy.checks):raise ContractError('AUDIT_REGRESSION_CHECK_COVERAGE')
        observations={}
        for raw,rule in zip(run['checks'],audit_policy.checks):
            fields(raw,CHECK_FIELDS,'AUDIT_CHECK_SCHEMA')
            equal(raw['check_id'],rule.check_id,'AUDIT_REGRESSION_CHECK_ORDER')
            equal(raw['validator_digest'],rule.validator_digest,'AUDIT_VALIDATOR_DRIFT')
            equal(raw['fixture_ids'],rule.fixture_ids,'AUDIT_CHECK_FIXTURE_SCOPE')
            cases=decode(raw['cases'],tuple[Observation,...])
            equal(tuple(c.case_id for c in cases),rule.case_ids,'AUDIT_CASE_COVERAGE')
            for c in cases:observations[(rule.check_id,c.case_id)]=c
        runs[phase]=observations
    if len(set(identities))!=2:raise ContractError('AUDIT_REUSED_EXECUTION')
    targets={(t.check_id,t.case_id) for t in audit_policy.targets};changes=[];problems=[]
    for key,before in runs['baseline'].items():
        after=runs['candidate'][key]
        if key in targets and before.status!='FAIL':problems.append(('AUDIT_TARGET_FAILURE_NOT_REPRODUCED',key))
        if key in targets and after.status!='PASS':problems.append(('AUDIT_TARGET_NOT_FIXED',key))
        if before.status=='PASS' and after.status!='PASS':problems.append(('AUDIT_NEW_REGRESSION',key))
        if after.status!='PASS':problems.append(('AUDIT_CANDIDATE_CASE_NOT_PASS',key))
        if before.status!=after.status or before.content_digest!=after.content_digest:
            changes.append(dict(check_id=key[0],case_id=key[1],before=before.status,after=after.status,
                before_witness=digest(before.witness),after_witness=digest(after.witness)))
    return dict(case_count=len(runs['baseline']),target_count=len(targets),changes=changes,
        problems=tuple(sorted(set(problems))),full_repository_regression_run=False,product_accepted=False)
