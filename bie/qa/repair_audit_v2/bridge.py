"""Re-audit actual inputs before issuing UNSIGNED full-regression NOT_RUN/FAIL."""
import hashlib
from ..release_v2.contracts import ContractError,ArtifactRef,GateEvidence,ReleaseCandidate,canonical_bytes,integer
from ..release_v2.policy import enterprise_policy
from ..source_v2.bridge import PreparedEvidence
from .evaluator import evaluate
from .models import candidate_for

def prepare_release_evidence(request,original_root,candidate_root,repair_policy,audit_policy,candidate,*,as_of,**reviews):
    integer(as_of,'as_of')
    if type(candidate) is not ReleaseCandidate:raise ContractError('AUDIT_RELEASE_TYPE')
    snapshot=candidate_for(request.snapshot,request.proposal)
    if (candidate.run_id,candidate.revision)!=(snapshot.run_id,snapshot.revision) or set(candidate.artifacts)!=set(snapshot.artifacts):
        raise ContractError('AUDIT_RELEASE_BINDING')
    result=evaluate(request,original_root,candidate_root,repair_policy,audit_policy,as_of=as_of,**reviews)
    data=canonical_bytes(result.to_dict());aid='qa16-repair-audit-regression'
    ref=ArtifactRef(aid,'qa_repair_audit_reports/'+candidate.content_digest+'/regression.json',hashlib.sha256(data).hexdigest(),len(data),'report')
    if aid in {a.artifact_id for a in candidate.artifacts} or ref.path in {a.path for a in candidate.artifacts}:raise ContractError('AUDIT_RELEASE_REPORT_ALIAS')
    rp=enterprise_policy()
    item=GateEvidence('2.0.0',aid,'regression',candidate.content_digest,rp.content_digest,candidate.run_id,candidate.revision,
        'FAIL' if result.status=='BLOCKED' else 'NOT_RUN','bie-qa-repair-audit-v2','1.0.0','review',
        tuple(sorted(a.artifact_id for a in snapshot.artifacts)),ref,as_of,as_of+3600,
        ('CANONICAL_FULL_REGRESSION_PENDING','UNSIGNED_LOCAL_REPAIR_AUDIT'),'UNSIGNED','')
    return PreparedEvidence(item,data)
