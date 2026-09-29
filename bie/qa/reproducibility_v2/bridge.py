"""Freshly audit bytes; emit unsigned FAIL or NOT_RUN, never full-product PASS."""
import hashlib
from ..release_v2.contracts import ContractError,ArtifactRef,GateEvidence,ReleaseCandidate,canonical_bytes
from ..release_v2.policy import enterprise_policy
from ..source_v2.bridge import PreparedEvidence
from .evaluator import evaluate

def prepare_release_evidence(request,source_root,evidence_root,policy,candidate,*,as_of,**reviews):
    if type(candidate) is not ReleaseCandidate:raise ContractError('REPRO_RELEASE_TYPE')
    # The reproduction job must explicitly contain every release artifact as input.
    # Similar run names or matching a single output are insufficient.
    if (candidate.run_id,candidate.revision)!=(request.source.run_id,request.source.revision):raise ContractError('REPRO_RELEASE_IDENTITY')
    if not set(candidate.artifacts)<=set(request.source.artifacts):raise ContractError('REPRO_RELEASE_ARTIFACT_COVERAGE')
    result=evaluate(request,source_root,evidence_root,policy,as_of=as_of,**reviews)
    data=canonical_bytes(result.to_dict());aid='qa16-reproducibility'
    ref=ArtifactRef(aid,'qa_repro_reports/'+candidate.content_digest+'/reproduction.json',hashlib.sha256(data).hexdigest(),len(data),'report')
    if aid in {a.artifact_id for a in candidate.artifacts} or ref.path in {a.path for a in candidate.artifacts}:raise ContractError('REPRO_RELEASE_ALIAS')
    rp=enterprise_policy()
    ev=GateEvidence('2.0.0',aid,'reproducibility',candidate.content_digest,rp.content_digest,candidate.run_id,candidate.revision,
        'FAIL' if result.status=='BLOCKED' else 'NOT_RUN','bie-qa-repro-v2','1.0.0','review',tuple(sorted(a.artifact_id for a in candidate.artifacts)),
        ref,as_of,as_of+3600,('FULL_PRODUCT_REPRODUCTION_PENDING','UNSIGNED_BOUNDED_RERUN'),'UNSIGNED','')
    return PreparedEvidence(ev,data)
