"""Exact diagnostic classification and operator-owned routes over inspected reports.

Message text and evaluator-supplied owner labels are never dispatch authority.
Unknown diagnostics are escalated. Authentication does not prove assessor quality.
"""
from dataclasses import asdict
from ..release_v2.contracts import ContractError,digest,integer,canonical_bytes
from ..source_v2.io import SnapshotStore
from ..source_v2.models import Finding
from ..source_v2.codec import loads
from ..reasoning_v2.attestation import Review,ReviewVerifier
from .models import Snapshot,FailureBatch,RepairPolicy,Failure,RepairPlan,Proposal
from .codec import decode

def approved(reviews, verifier, *, subject, purpose, request_digest, policy, evidence_ids, now):
    if type(verifier) is not ReviewVerifier:raise ContractError('REPAIR_VERIFIER_TYPE')
    if type(reviews) is not tuple or len(reviews)>128 or any(type(r) is not Review for r in reviews):raise ContractError('REPAIR_REVIEWS_TYPE')
    if len({r.review_id for r in reviews})!=len(reviews):raise ContractError('REPAIR_DUPLICATE_REVIEW')
    votes=set();bad=[]
    for r in reviews:
        if (r.subject_id,r.purpose)!=(subject,purpose):bad.append('REPAIR_UNEXPECTED_REVIEW');continue
        auth=verifier.verify_bound(r,request_digest,policy.content_digest,policy.max_receipt_age_seconds,now)
        if tuple(sorted(r.evidence_ids))!=tuple(sorted(evidence_ids)):bad.append('REPAIR_REVIEW_EVIDENCE');continue
        if not auth.authenticated:bad.append('REPAIR_'+auth.code)
        elif not auth.operational:bad.append('REPAIR_TEST_ONLY_REVIEW')
        elif r.verdict!='VERIFIED':bad.append('REPAIR_REVIEW_'+r.verdict)
        elif r.confidence_ppm!=1000000:bad.append('REPAIR_REVIEW_NOT_EXPLICIT_APPROVAL')
        else:votes.add(auth.independence_group)
    if not votes:bad.append('REPAIR_APPROVAL_REQUIRED')
    return not bad,tuple(sorted(set(bad)))

REPORT_FIELDS={'task_id','request_digest','policy_digest','evidence_digest','evaluated_at','findings','measurements','inspected_artifact_ids','limitations','status','product_accepted'}

def inspect_report(data, binding, allowed_ids, now, max_age):
    obj=loads(data)
    if type(obj) is not dict or set(obj)!=REPORT_FIELDS:raise ContractError('REPAIR_REPORT_SCHEMA')
    if obj['product_accepted'] is not False:raise ContractError('REPAIR_REPORT_ACCEPTANCE_CLAIM')
    if (obj['task_id'],obj['request_digest'],obj['policy_digest'])!=(binding.task_id,binding.request_digest,binding.evaluator_policy_digest):raise ContractError('REPAIR_REPORT_BINDING')
    from ..release_v2.contracts import sha256,token
    sha256(obj['evidence_digest'],'evidence_digest');integer(obj['evaluated_at'],'evaluated_at')
    if not 0<=now-obj['evaluated_at']<=max_age:raise ContractError('REPAIR_REPORT_STALE')
    for key in ('findings','measurements','inspected_artifact_ids','limitations'):
        if type(obj[key]) is not list or len(obj[key])>4096:raise ContractError('REPAIR_REPORT_COLLECTION')
    if not obj['inspected_artifact_ids'] or len(set(obj['inspected_artifact_ids']))!=len(obj['inspected_artifact_ids']) or not set(obj['inspected_artifact_ids'])<=allowed_ids:raise ContractError('REPAIR_REPORT_INSPECTED_SCOPE')
    for x in obj['inspected_artifact_ids']:token(x,'inspected_artifact')
    for item in obj['measurements']:
        if type(item) is not list or len(item)!=2:raise ContractError('REPAIR_REPORT_MEASUREMENT')
        token(item[0],'measurement');integer(item[1],'value',-(2**53-1),2**53-1)
    if len({x[0] for x in obj['measurements']})!=len(obj['measurements']):raise ContractError('REPAIR_REPORT_DUPLICATE_MEASUREMENT')
    if any(type(s) is not str or len(s)>8192 for s in obj['limitations']):raise ContractError('REPAIR_REPORT_LIMITATIONS')
    findings=tuple(decode(f,Finding) for f in obj['findings'])
    if len({(f.code,f.subject_id,f.severity) for f in findings})!=len(findings):raise ContractError('REPAIR_DUPLICATE_FINDING')
    status='BLOCKED' if any(f.severity=='BLOCKER' for f in findings) else 'REVIEW_REQUIRED' if any(f.severity=='REVIEW' for f in findings) else 'CHECKS_PASSED'
    if obj['status']!=status:raise ContractError('REPAIR_REPORT_STATUS_MISMATCH')
    return findings

def classify(batch,snapshot,artifact_root,policy,*,as_of,reviews=(),verifier=None):
    if type(batch) is not FailureBatch or type(snapshot) is not Snapshot or type(policy) is not RepairPolicy:raise ContractError('REPAIR_PLAN_TYPE')
    integer(as_of,'as_of')
    if (batch.run_id,batch.revision,batch.snapshot_digest)!=(snapshot.run_id,snapshot.revision,snapshot.content_digest):raise ContractError('REPAIR_BATCH_BINDING')
    if {a.path for a in snapshot.artifacts}&{r.artifact.path for r in batch.reports} or {a.artifact_id for a in snapshot.artifacts}&{r.artifact.artifact_id for r in batch.reports}:raise ContractError('REPAIR_REPORT_ALIAS')
    rules={(r.task_id,r.code):r for r in policy.rules};failures=[];ids=[];diagnostics=[]
    ok,codes=approved(reviews,ReviewVerifier() if verifier is None else verifier,subject='repair-findings',purpose='inventory',request_digest=batch.content_digest,policy=policy,evidence_ids=tuple(r.artifact.artifact_id for r in batch.reports),now=as_of)
    diagnostics.extend(codes)
    with SnapshotStore(artifact_root) as store:
        for a in snapshot.artifacts:store.read(a)
        for b in batch.reports:
            data=store.read(b.artifact);fs=inspect_report(data,b,{a.artifact_id for a in snapshot.artifacts},as_of,policy.max_receipt_age_seconds);ids.append(b.artifact.artifact_id)
            for f in fs:
                if f.severity=='INFO':continue
                rule=rules.get((b.task_id,f.code))
                category=rule.category if rule else 'UNKNOWN';owner=rule.owner if rule else 'QA'
                # A REVIEW finding is never permission to change uncertain content.
                automatic=bool(rule and rule.automatic and f.severity=='BLOCKER')
                fid='failure-'+digest(dict(task=b.task_id,code=f.code,subject=f.subject_id,report=b.artifact.sha256))[:32]
                failures.append(Failure(fid,b.task_id,f.code,f.subject_id,f.severity,category,owner,automatic,b.artifact.sha256))
    return RepairPlan(batch.content_digest,snapshot.content_digest,policy.content_digest,tuple(sorted(failures,key=lambda f:f.failure_id)),tuple(sorted(ids)),ok,tuple(sorted(set(diagnostics))))

def check_closure(policy,owner):
    """Changed owner checks invalidate all descendants; include all dependencies."""
    route=next((r for r in policy.routes if r.owner==owner),None)
    if route is None:raise ContractError('REPAIR_OWNER_UNAVAILABLE')
    graph={c.check_id:set(c.dependencies) for c in policy.checks};affected=set(route.check_ids)
    while True:
        newer=affected|{k for k,v in graph.items() if v&affected}
        if newer==affected:break
        affected=newer
    required=affected|set(policy.required_checks)
    while True:
        newer=required|{d for k in required for d in graph[k]}
        if newer==required:break
        required=newer
    ordered=[]
    while len(ordered)<len(required):
        ready=sorted(k for k in required-set(ordered) if graph[k]<=set(ordered))
        if not ready:raise ContractError('REPAIR_CHECK_CYCLE')
        ordered.extend(ready)
    return tuple(ordered),tuple(sorted(affected))

def route_summary(plan,policy):
    if type(plan) is not RepairPlan or type(policy) is not RepairPolicy or plan.policy_digest!=policy.content_digest:raise ContractError('REPAIR_ROUTE_BINDING')
    owners=sorted({f.owner for f in plan.failures});rows=[]
    for owner in owners:
        fs=[f for f in plan.failures if f.owner==owner]
        can=plan.authenticated and not plan.diagnostics and any(f.automatic for f in fs)
        checks,invalidated=check_closure(policy,owner) if can else ((),())
        rows.append(dict(owner=owner,failure_ids=[f.failure_id for f in fs],action='REQUEST_DATA_ONLY_PROPOSAL' if can else 'ESCALATE_NO_ARTIFACT_MUTATION',required_checks=checks,invalidated_checks=invalidated,dispatch_performed=False))
    return dict(plan_digest=plan.content_digest,routes=rows,product_accepted=False)

def validate_proposal(proposal,plan,snapshot,policy):
    if type(proposal) is not Proposal or type(plan) is not RepairPlan or type(snapshot) is not Snapshot or type(policy) is not RepairPolicy:raise ContractError('REPAIR_PROPOSAL_TYPE')
    if (proposal.run_id,proposal.revision,proposal.base_digest,proposal.policy_digest,proposal.plan_digest)!=(snapshot.run_id,snapshot.revision,snapshot.content_digest,policy.content_digest,plan.content_digest):raise ContractError('REPAIR_PROPOSAL_BINDING')
    if (plan.snapshot_digest,plan.policy_digest)!=(snapshot.content_digest,policy.content_digest) or not plan.authenticated or plan.diagnostics:raise ContractError('REPAIR_PLAN_NOT_AUTHORIZED')
    failures={f.failure_id:f for f in plan.failures}
    for fid in proposal.target_failure_ids:
        f=failures.get(fid)
        if f is None or f.owner!=proposal.owner or not f.automatic:raise ContractError('REPAIR_TARGET_NOT_AUTHORIZED')
    route=next((r for r in policy.routes if r.owner==proposal.owner),None)
    if route is None:raise ContractError('REPAIR_OWNER_UNAVAILABLE')
    current={a.path:a for a in snapshot.artifacts}
    if len(proposal.replacements)>policy.max_changed_files:raise ContractError('REPAIR_CHANGED_FILE_LIMIT')
    if sum(r.artifact.size for r in proposal.replacements)>policy.max_replacement_bytes:raise ContractError('REPAIR_REPLACEMENT_LIMIT')
    for r in proposal.replacements:
        a=current.get(r.path)
        if r.path not in route.mutable_paths or a is None or a.role in ('source','report'):raise ContractError('REPAIR_PATH_NOT_OWNED')
        if a.sha256!=r.before_sha256:raise ContractError('REPAIR_STALE_BEFORE_HASH')
        if a.sha256==r.artifact.sha256:raise ContractError('REPAIR_NO_OP')
    return check_closure(policy,proposal.owner)
