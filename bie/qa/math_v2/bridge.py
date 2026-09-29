"""Unsigned, content-bound release connection. Text QA is never rendered-media QA."""
import hashlib
from ..release_v2.contracts import ArtifactRef,GateEvidence,ReleaseCandidate,ContractError,canonical_bytes
from ..release_v2.policy import ReleasePolicy,enterprise_policy
from ..source_v2.bridge import PreparedEvidence
from .models import MathRequest,MathPolicy
from .evaluator import evaluate

def prepare_release_evidence(request,candidate,artifact_root,policy,*,as_of,release_policy=None,**options):
    if type(request) is not MathRequest or type(candidate) is not ReleaseCandidate or type(policy) is not MathPolicy:raise ContractError('INVALID_MATH_BRIDGE_INPUT')
    s=request.source
    if (s.candidate_digest,s.run_id,s.revision)!=(candidate.content_digest,candidate.run_id,candidate.revision):raise ContractError('MATH_CANDIDATE_BINDING_MISMATCH')
    idx={a.artifact_id:a for a in candidate.artifacts};refs=[x.artifact for x in s.sources]+[x.artifact for x in s.outputs]
    if any(idx.get(a.artifact_id)!=a for a in refs):raise ContractError('MATH_CANDIDATE_ARTIFACT_MISMATCH')
    if {a.artifact_id for a in candidate.artifacts if a.role=='source'}!={x.artifact.artifact_id for x in s.sources}:raise ContractError('MATH_CANDIDATE_SOURCE_COVERAGE')
    rp=enterprise_policy() if release_policy is None else release_policy
    if type(rp) is not ReleasePolicy:raise ContractError('INVALID_RELEASE_POLICY')
    result=evaluate(request,artifact_root,policy,as_of=as_of,**options)
    inspected=result.formula.inspected_artifact_ids
    if not inspected:raise ContractError('NO_VERIFIED_MATH_ARTIFACTS')
    payload=canonical_bytes(dict(gate='mathematical_correctness',typed_text_math=result.to_dict(),actual_media_evaluated=False,product_accepted=False))
    aid='qa16-mathematical-correctness-report';path=f'qa_math_reports/{request.content_digest}/mathematical_correctness.json'
    if aid in idx or path in {a.path for a in candidate.artifacts}:raise ContractError('MATH_REPORT_COLLISION')
    ref=ArtifactRef(aid,path,hashlib.sha256(payload).hexdigest(),len(payload),'report')
    status='FAIL' if result.status=='BLOCKED' else 'NOT_RUN'
    codes=tuple(sorted({f.code for r in (result.formula,result.derivation,result.numerical,result.units) for f in r.findings if f.severity!='INFO'}))[:124]+('ACTUAL_MEDIA_MATH_NOT_EVALUATED','UNSIGNED_REVIEW_EVIDENCE')
    gate=GateEvidence('2.0.0','qa16-mathematical-correctness','mathematical_correctness',candidate.content_digest,rp.content_digest,candidate.run_id,candidate.revision,
        status,'bie-qa-math-v2','1.0.0','review',inspected,ref,as_of,as_of+min(3600,policy.max_receipt_age_seconds,rp.max_evidence_lifetime_seconds),codes,'UNSIGNED','')
    return PreparedEvidence(gate,payload)
