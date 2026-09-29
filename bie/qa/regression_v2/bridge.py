"""Recheck inputs; emit unsigned FAIL or NOT_RUN, never full-regression PASS."""
import hashlib
from ..release_v2.contracts import ContractError,ArtifactRef,GateEvidence,ReleaseCandidate,canonical_bytes
from ..release_v2.policy import enterprise_policy
from ..source_v2.bridge import PreparedEvidence
from .evaluator import evaluate

def prepare_release_evidence(request,baseline_root,candidate_root,evidence_root,policy,candidate,*,as_of,**reviews):
    if type(candidate) is not ReleaseCandidate:raise ContractError('REG_RELEASE_TYPE')
    if (candidate.run_id,candidate.revision)!=(request.candidate.run_id,request.candidate.revision) or set(candidate.artifacts)!=set(request.candidate.artifacts):raise ContractError('REG_RELEASE_BINDING')
    result=evaluate(request,baseline_root,candidate_root,evidence_root,policy,as_of=as_of,**reviews)
    data=canonical_bytes(result.to_dict());aid='qa16-regression-suite'
    ref=ArtifactRef(aid,'qa_regression_reports/'+candidate.content_digest+'/regression.json',hashlib.sha256(data).hexdigest(),len(data),'report')
    if aid in {a.artifact_id for a in candidate.artifacts} or ref.path in {a.path for a in candidate.artifacts}:raise ContractError('REG_RELEASE_ALIAS')
    rp=enterprise_policy()
    ev=GateEvidence('2.0.0',aid,'regression',candidate.content_digest,rp.content_digest,candidate.run_id,candidate.revision,
        'FAIL' if result.status=='BLOCKED' else 'NOT_RUN','bie-qa-regression-v2','1.0.0','review',tuple(sorted(a.artifact_id for a in candidate.artifacts)),ref,as_of,as_of+3600,
        ('CANONICAL_FULL_REGRESSION_PENDING','UNSIGNED_BOUNDED_COMPARISON'),'UNSIGNED','')
    return PreparedEvidence(ev,data)
