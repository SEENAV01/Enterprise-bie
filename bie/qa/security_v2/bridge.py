"""Unsigned, non-releasing security evidence. Fixed probes never grant full PASS."""
import hashlib
from ..release_v2.contracts import ContractError,ArtifactRef,GateEvidence,ReleaseCandidate,canonical_bytes
from ..release_v2.policy import enterprise_policy
from ..source_v2.bridge import PreparedEvidence
from .evaluator import evaluate

def prepare_release_evidence(request,root,policy,candidate,*,as_of,**options):
    if type(candidate) is not ReleaseCandidate:raise ContractError('SEC_RELEASE_TYPE')
    if (candidate.run_id,candidate.revision)!=(request.snapshot.run_id,request.snapshot.revision):raise ContractError('SEC_RELEASE_IDENTITY')
    if not set(candidate.artifacts)<=set(request.snapshot.artifacts):raise ContractError('SEC_RELEASE_COVERAGE')
    result=evaluate(request,root,policy,as_of=as_of,**options);data=canonical_bytes(result.to_dict());aid='qa16-security'
    ref=ArtifactRef(aid,'qa_security_reports/'+candidate.content_digest+'/security.json',hashlib.sha256(data).hexdigest(),len(data),'report')
    if aid in {a.artifact_id for a in candidate.artifacts} or ref.path in {a.path for a in candidate.artifacts}:raise ContractError('SEC_RELEASE_ALIAS')
    p=enterprise_policy()
    ev=GateEvidence('2.0.0',aid,'security',candidate.content_digest,p.content_digest,candidate.run_id,candidate.revision,
        'FAIL' if result.status=='BLOCKED' else 'NOT_RUN','bie-qa-security-v2','1.0.0','execution',tuple(sorted(a.artifact_id for a in candidate.artifacts)),ref,
        as_of,as_of+3600,('FULL_NATIVE_SECURITY_RUNTIME_PENDING','UNSIGNED_BOUNDED_SECURITY_QA'),'UNSIGNED','')
    return PreparedEvidence(ev,data)
