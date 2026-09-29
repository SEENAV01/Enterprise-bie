"""Unsigned evidence only; bounded rights data never certifies the full release."""
import hashlib
from ..release_v2.contracts import ContractError,ArtifactRef,GateEvidence,ReleaseCandidate,canonical_bytes
from ..release_v2.policy import enterprise_policy
from ..source_v2.bridge import PreparedEvidence
from .evaluator import evaluate

def prepare_release_evidence(request,root,policy,candidate,*,as_of,**reviews):
    if type(candidate) is not ReleaseCandidate:raise ContractError('RIGHTS_RELEASE_TYPE')
    if (candidate.run_id,candidate.revision)!=(request.snapshot.run_id,request.snapshot.revision):raise ContractError('RIGHTS_RELEASE_IDENTITY')
    if not set(candidate.artifacts)<=set(request.snapshot.artifacts):raise ContractError('RIGHTS_RELEASE_ARTIFACT_COVERAGE')
    outputs={u.output_artifact_id for u in policy.requirements}
    sources={m.artifact_id for m in policy.materials if m.category=='SOURCE'}
    if any(a.artifact_id not in (sources if a.role=='source' else outputs) for a in candidate.artifacts):raise ContractError('RIGHTS_RELEASE_USE_COVERAGE')
    result=evaluate(request,root,policy,as_of=as_of,**reviews);data=canonical_bytes(result.to_dict());aid='qa16-rights'
    ref=ArtifactRef(aid,'qa_rights_reports/'+candidate.content_digest+'/rights.json',hashlib.sha256(data).hexdigest(),len(data),'report')
    if aid in {a.artifact_id for a in candidate.artifacts} or ref.path in {a.path for a in candidate.artifacts}:raise ContractError('RIGHTS_RELEASE_ALIAS')
    p=enterprise_policy()
    ev=GateEvidence('2.0.0',aid,'rights_and_asset_provenance',candidate.content_digest,p.content_digest,candidate.run_id,candidate.revision,
        'FAIL' if result.status=='BLOCKED' else 'NOT_RUN','bie-qa-rights-v2','1.0.0','review',tuple(sorted(a.artifact_id for a in candidate.artifacts)),ref,
        as_of,as_of+3600,('FULL_RELEASE_RIGHTS_REVIEW_PENDING','UNSIGNED_BOUNDED_RIGHTS_QA'),'UNSIGNED','')
    return PreparedEvidence(ev,data)
