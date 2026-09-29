"""Unsigned release-v2 connection. Text PR/RE success is not video/game proof."""
import hashlib
from ..release_v2.contracts import ArtifactRef,GateEvidence,ReleaseCandidate,ContractError,canonical_bytes
from ..release_v2.policy import ReleasePolicy,enterprise_policy
from ..source_v2.bridge import PreparedEvidence
from .models import ReasoningRequest,ReasoningPolicy
from .evaluator import evaluate


def prepare_release_evidence(request:ReasoningRequest,candidate:ReleaseCandidate,artifact_root,policy:ReasoningPolicy,*,as_of:int,
                             release_policy:ReleasePolicy|None=None,**options):
    if type(request) is not ReasoningRequest or type(candidate) is not ReleaseCandidate or type(policy) is not ReasoningPolicy:raise ContractError('INVALID_REASONING_BRIDGE_INPUT')
    s=request.source
    if (s.candidate_digest,s.run_id,s.revision)!=(candidate.content_digest,candidate.run_id,candidate.revision):raise ContractError('REASONING_CANDIDATE_BINDING_MISMATCH')
    refs=[x.artifact for x in s.sources]+[x.artifact for x in s.outputs]+[x.artifact for x in request.masteries]+[x.artifact for x in request.calibrations]
    idx={x.artifact_id:x for x in candidate.artifacts}
    if any(idx.get(x.artifact_id)!=x for x in refs):raise ContractError('REASONING_CANDIDATE_ARTIFACT_MISMATCH')
    if {x.artifact_id for x in candidate.artifacts if x.role=='source'}!={x.artifact.artifact_id for x in s.sources}:raise ContractError('REASONING_CANDIDATE_SOURCE_COVERAGE')
    rp=enterprise_policy() if release_policy is None else release_policy
    if type(rp) is not ReleasePolicy:raise ContractError('INVALID_RELEASE_POLICY')
    result=evaluate(request,artifact_root,policy,as_of=as_of,**options)
    inspected=result.prerequisite.inspected_artifact_ids
    if not inspected:raise ContractError('NO_VERIFIED_REASONING_ARTIFACTS')
    output=[]
    for gate,reports in (('prerequisite_correctness',(result.prerequisite,)),('reasoning_validity',(result.validity,result.evidence,result.uncertainty))):
        payload=canonical_bytes(dict(gate=gate,typed_text_reasoning=result.to_dict(),actual_media_evaluated=False,product_accepted=False))
        aid=f'qa16-{gate}-report';path=f'qa_reasoning_reports/{request.content_digest}/{gate}.json'
        if aid in idx or path in {x.path for x in candidate.artifacts}:raise ContractError('REASONING_REPORT_COLLISION')
        ref=ArtifactRef(aid,path,hashlib.sha256(payload).hexdigest(),len(payload),'report')
        # Even signatures supplied downstream cannot promote missing media scope.
        status='FAIL' if any(x.status=='BLOCKED' for x in reports) else 'NOT_RUN'
        codes=tuple(sorted({f.code for r in reports for f in r.findings if f.severity!='INFO'}))[:124]+('ACTUAL_MEDIA_PR_RE_NOT_EVALUATED','UNSIGNED_REVIEW_EVIDENCE')
        envelope=GateEvidence('2.0.0',f'qa16-{gate}',gate,candidate.content_digest,rp.content_digest,candidate.run_id,candidate.revision,
            status,'bie-qa-reasoning-v2','1.0.0','review',inspected,ref,as_of,
            as_of+min(3600,policy.max_receipt_age_seconds,rp.max_evidence_lifetime_seconds),codes,'UNSIGNED','')
        output.append(PreparedEvidence(envelope,payload))
    return tuple(output)
