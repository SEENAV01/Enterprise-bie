"""Candidate-bound unsigned evidence. Text-plan checks never certify a video."""
import hashlib
from ..release_v2.contracts import ArtifactRef, GateEvidence, ReleaseCandidate, ContractError, canonical_bytes
from ..release_v2.policy import ReleasePolicy, enterprise_policy
from ..source_v2.bridge import PreparedEvidence
from .models import VisualRequest, VisualPolicy
from .evaluator import evaluate, AREAS


def prepare_release_evidence(request, candidate, artifact_root, policy, *, as_of, release_policy=None, **options):
    if type(request) is not VisualRequest or type(candidate) is not ReleaseCandidate or type(policy) is not VisualPolicy:
        raise ContractError('VIS_BRIDGE_INPUT_TYPE')
    s = request.source
    if (s.candidate_digest, s.run_id, s.revision) != (candidate.content_digest, candidate.run_id, candidate.revision):
        raise ContractError('VIS_CANDIDATE_BINDING_MISMATCH')
    idx = {a.artifact_id: a for a in candidate.artifacts}
    refs = [x.artifact for x in s.sources] + [x.artifact for x in s.outputs]
    refs += [a for c in request.captures for a in (c.html,c.measurements,c.screenshot)]
    if any(idx.get(a.artifact_id) != a for a in refs): raise ContractError('VIS_CANDIDATE_ARTIFACT_MISMATCH')
    if {a.artifact_id for a in candidate.artifacts if a.role == 'source'} != {x.artifact.artifact_id for x in s.sources}:
        raise ContractError('VIS_CANDIDATE_SOURCE_COVERAGE')
    rp = enterprise_policy() if release_policy is None else release_policy
    if type(rp) is not ReleasePolicy: raise ContractError('VIS_RELEASE_POLICY_TYPE')
    result = evaluate(request, artifact_root, policy, as_of=as_of, **options)
    inspected = result.layout.inspected_artifact_ids
    if not inspected: raise ContractError('VIS_NO_INSPECTED_ARTIFACTS')
    payload = canonical_bytes(dict(gate='visual_quality', declared_visual_plan=result.to_dict(),
                                   actual_media_evaluated=False, product_accepted=False))
    aid = 'qa16-visual-quality-report'
    path = f'qa_visual_reports/{request.content_digest}/visual_quality.json'
    if aid in idx or path in {a.path for a in candidate.artifacts}: raise ContractError('VIS_REPORT_COLLISION')
    ref = ArtifactRef(aid, path, hashlib.sha256(payload).hexdigest(), len(payload), 'report')
    status = 'FAIL' if result.status == 'BLOCKED' else 'NOT_RUN'
    codes = tuple(sorted({f.code for area in AREAS for f in getattr(result, area).findings if f.severity != 'INFO'}))[:124] + ('ACTUAL_MEDIA_VIS_NOT_EVALUATED', 'UNSIGNED_REVIEW_EVIDENCE')
    gate = GateEvidence('2.0.0', 'qa16-visual-quality', 'visual_quality', candidate.content_digest,
                       rp.content_digest, candidate.run_id, candidate.revision, status, 'bie-qa-visual-v2',
                       '1.0.0', 'review', inspected, ref, as_of,
                       as_of + min(3600, policy.max_receipt_age_seconds, rp.max_evidence_lifetime_seconds), codes, 'UNSIGNED', '')
    return PreparedEvidence(gate, payload)
