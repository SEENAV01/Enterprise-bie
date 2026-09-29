"""Read actual bytes and report each regression family without granting release."""
from dataclasses import asdict,dataclass
from pathlib import Path
from ..release_v2.contracts import ContractError,digest,integer,canonical_bytes,token
from ..source_v2.io import SnapshotStore
from ..source_v2.models import Report,Finding
from ..source_v2.codec import loads
from ..repair_v2.codec import decode
from ..repair_v2.planner import approved
from ..repair_audit_v2.io import verify_files,fields,equal
from ..reasoning_v2.attestation import ReviewVerifier
from .models import RegressionRequest,RegressionPolicy,Observation,binding
from .runner import obligations
from .diffs import artifact_diff,semantic_diff,visual_diff,game_diff
LIMITS=(
    'Only explicitly registered cases and declared artifacts are compared; not full canonical regression.',
    'Semantic comparison uses typed records, not automatic language entailment or factual verification.',
    'PNG samples do not establish unsampled frames or cinematic teaching quality.',
    'Game traces are finite; equal state is not observed learning or native runtime acceptance.',
    'Hashes need independent operator trust. Validator isolation is not a hostile-code sandbox.',
    'No release, GitHub integration, Section15 acceptance or real-book E2E is authorized here.'
)

@dataclass(frozen=True,slots=True)
class Result:
    reports: tuple[Report,...]
    diff_json: str
    @property
    def status(self):
        states={r.status for r in self.reports}
        return 'BLOCKED' if 'BLOCKED' in states else 'REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in states else 'CHECKS_PASSED'
    def to_dict(self):return dict(schema_version='bie.qa.regression-result/1',reports=[r.to_dict() for r in self.reports],diff=loads(self.diff_json.encode()),status=self.status,product_accepted=False,full_repository_regression_run=False)

def inspect_execution(o,request,policy,as_of):
    fields(o,{'schema_version','binding','evaluated_at','environment','environment_digest','baseline','candidate','full_repository_regression_run','product_accepted'},'REG_EXECUTION_SCHEMA')
    if o['schema_version']!='bie.qa.regression-execution/1' or o['product_accepted'] is not False or o['full_repository_regression_run'] is not False:raise ContractError('REG_EXECUTION_SCOPE')
    equal(o['binding'],binding(request.comparison_id,request.baseline,request.candidate,policy),'REG_EXECUTION_BINDING')
    integer(o['evaluated_at'],'evaluated_at')
    if not 0<=as_of-o['evaluated_at']<=policy.max_receipt_age_seconds:raise ContractError('REG_EXECUTION_STALE')
    if type(o['environment']) is not dict or not o['environment']:raise ContractError('REG_ENVIRONMENT_EMPTY')
    equal(digest(o['environment']),o['environment_digest'],'REG_ENVIRONMENT_HASH')
    outcomes={};issues=[]
    for name,snap in (('baseline',request.baseline),('candidate',request.candidate)):
        p=o[name]
        fields(p,{'phase','snapshot_digest','execution_id','executed_at','wall_started_ns','wall_finished_ns','elapsed_ms','worker_executed','process_exit','error','checks'},'REG_PHASE_SCHEMA')
        equal((p['phase'],p['snapshot_digest'],p['executed_at']),(name,snap.content_digest,o['evaluated_at']),'REG_PHASE_BINDING')
        token(p['execution_id'],'execution_id')
        if p['worker_executed'] is not True or type(p['process_exit']) is not int or p['process_exit']!=0:raise ContractError('REG_PHASE_NOT_EXECUTED')
        for f in ('wall_started_ns','wall_finished_ns'):integer(p[f],f,1,2**63-1)
        integer(p['elapsed_ms'],'elapsed_ms',0,(policy.phase_timeout_seconds+5)*1000)
        if p['wall_finished_ns']<p['wall_started_ns']:raise ContractError('REG_PHASE_CLOCK')
        if type(p['error']) is not str or p['error']:raise ContractError('REG_PHASE_ERROR')
        if type(p['checks']) is not list or len(p['checks'])!=len(policy.checks):raise ContractError('REG_CHECK_COVERAGE')
        found={}
        for rule,row in zip(policy.checks,p['checks']):
            fields(row,{'check_id','validator_digest','fixture_ids','cases'},'REG_CHECK_SCHEMA')
            equal((row['check_id'],row['validator_digest'],row['fixture_ids']),(rule.check_id,rule.validator_digest,rule.fixture_ids),'REG_CHECK_IDENTITY')
            cases=decode(row['cases'],tuple[Observation,...])
            if tuple(c.case_id for c in cases)!=rule.case_ids:raise ContractError('REG_CASE_COVERAGE')
            for c in cases:found[(rule.check_id,c.case_id)]=c
        outcomes[name]=found
    if o['baseline']['execution_id']==o['candidate']['execution_id']:raise ContractError('REG_EXECUTION_REUSED')
    # The collector is sequential. A claimed after-run before baseline completion is invalid.
    if o['candidate']['wall_started_ns']<o['baseline']['wall_finished_ns']:raise ContractError('REG_PHASE_ORDER')
    for key,after in outcomes['candidate'].items():
        before=outcomes['baseline'][key]
        if before.status not in ('PASS','FAIL'):issues.append(('REG_BASELINE_CASE_UNVERIFIED',':'.join(key)))
        if after.status!='PASS':issues.append(('REG_CANDIDATE_CASE_FAILED',':'.join(key)))
        if before.status=='PASS' and after.status!='PASS':issues.append(('REG_PREVIOUS_PASS_REGRESSED',':'.join(key)))
    return dict(case_pairs=len(outcomes['candidate']),new_regressions=sum(c=='REG_PREVIOUS_PASS_REGRESSED' for c,_ in issues)),issues

def evaluate(request,baseline_root,candidate_root,evidence_root,policy,*,as_of,reviews=(),verifier=None):
    if type(request) is not RegressionRequest or type(policy) is not RegressionPolicy:raise ContractError('REG_INPUT_TYPE')
    integer(as_of,'as_of');verifier=ReviewVerifier() if verifier is None else verifier
    from ..reasoning_v2.attestation import Review
    if type(reviews) is not tuple or any(type(r) is not Review for r in reviews) or len(reviews)>128 or len({r.review_id for r in reviews})!=len(reviews):raise ContractError('REG_REVIEW_COLLECTION')
    fs=[[] for _ in range(5)];diff={};inspected=set();measure=[[] for _ in range(5)]
    def add(i,code,subject='comparison',severity='BLOCKER'):
        f=Finding(code,severity,subject,'QA','Regression requirement: '+code)
        if f not in fs[i]:fs[i].append(f)
    def authorize(indices,subject,purpose,evidence_ids):
        relevant=tuple(r for r in reviews if (r.subject_id,r.purpose)==(subject,purpose))
        ok,codes=approved(relevant,verifier,subject=subject,purpose=purpose,request_digest=request.content_digest,policy=policy,evidence_ids=evidence_ids,now=as_of)
        if not ok:
            for i in indices:add(i,'REG_REVIEW_AUTH_REQUIRED',subject,'REVIEW')
        return ok
    try:
        a=Path(baseline_root).resolve();b=Path(candidate_root).resolve();e=Path(evidence_root).resolve()
        if a==b or a.is_relative_to(b) or b.is_relative_to(a):raise ContractError('REG_ROOT_OVERLAP')
        if any(e==r or e.is_relative_to(r) or r.is_relative_to(e) for r in (a,b)):raise ContractError('REG_EVIDENCE_ROOT_OVERLAP')
        before,after=obligations(request.baseline,request.candidate,policy)
        verify_files(baseline_root,request.baseline,exact=True);verify_files(candidate_root,request.candidate,exact=True)
        ids=tuple(sorted(set(before)|set(after)));inspected.update(ids)
        allowed_targets={('regression-inventory','inventory'),('regression-execution','support')}|{('semantic-'+r.artifact_id,'mapping') for r in policy.semantic}
        if any((r.subject_id,r.purpose) not in allowed_targets for r in reviews):raise ContractError('REG_UNEXPECTED_REVIEW')
        authorize(range(5),'regression-inventory','inventory',ids)
    except (ContractError,OSError) as ex:
        for i in range(5):add(i,ex.code if isinstance(ex,ContractError) else 'REG_INPUT_IO')
        before=after=None
    if before is not None:
        try:
            with SnapshotStore(evidence_root) as st:
                if request.execution.size>policy.max_evidence_bytes:raise ContractError('REG_EXECUTION_SIZE')
                execution=loads(st.read(request.execution));inspected.add(request.execution.artifact_id)
            stats,problems=inspect_execution(execution,request,policy,as_of);measure[0]=sorted(stats.items())
            for code,sub in problems:add(0,code,sub)
            authorize((0,),'regression-execution','support',(request.execution.artifact_id,))
            diff['execution']=stats
        except (ContractError,OSError) as ex:
            add(0,ex.code if isinstance(ex,ContractError) else 'REG_EXECUTION_IO')
        changes,issues=artifact_diff(request.baseline,request.candidate,policy);diff['artifacts']=changes;measure[1]=[('changed_artifacts',len(changes))]
        for code,sub in issues:add(1,code,sub)
        for i,name,fun in ((2,'semantic',semantic_diff),(3,'visual',visual_diff),(4,'game',game_diff)):
            diff[name]={}
            # One bounded reader per comparison pair; aggregate budget already
            # enforced by Snapshot plus initial verify_files on each complete set.
            for rule in getattr(policy,name):
                try:
                    with SnapshotStore(baseline_root) as left,SnapshotStore(candidate_root) as right:
                        result,issues=fun(left.read(before[rule.artifact_id]),right.read(after[rule.artifact_id]),rule)
                    diff[name][rule.artifact_id]=result
                    for code,severity,sub in issues:add(i,code,sub,severity)
                    if name=='semantic':authorize((i,),'semantic-'+rule.artifact_id,'mapping',(rule.artifact_id,))
                except (ContractError,OSError,KeyError) as ex:add(i,ex.code if isinstance(ex,ContractError) else 'REG_DIFF_INPUT',rule.artifact_id)
            measure[i]=[('compared_artifacts',len(diff[name]))]
        try:
            verify_files(baseline_root,request.baseline,exact=True);verify_files(candidate_root,request.candidate,exact=True)
            with SnapshotStore(evidence_root) as s:s.read(request.execution)
        except (ContractError,OSError) as ex:
            for i in range(5):add(i,'REG_INPUT_CHANGED_DURING_EVALUATION')
    evidence_digest=digest(dict(request=request.content_digest,policy=policy.content_digest,verifier=verifier.configuration_digest))
    reports=tuple(Report('BIE-QA-REG-'+str(i+1).zfill(3),request.content_digest,policy.content_digest,evidence_digest,as_of,
        tuple(sorted(fs[i],key=lambda f:(f.severity,f.code,f.subject_id))),tuple(measure[i]),tuple(sorted(inspected)),LIMITS) for i in range(5))
    return Result(reports,canonical_bytes(diff).decode())
