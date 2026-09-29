"""Candidate-bound unsigned evidence. Inspected PCM and caption checks never certify the final audiovisual product."""
import hashlib
from ..release_v2.contracts import ArtifactRef, GateEvidence, ReleaseCandidate, ContractError, canonical_bytes
from ..release_v2.policy import ReleasePolicy, enterprise_policy
from ..source_v2.bridge import PreparedEvidence
from .models import AudioRequest, AudioPolicy, all_refs
from .evaluator import evaluate, AREAS


def prepare_release_evidence(request, candidate, artifact_root, policy, *, as_of, release_policy=None, **options):
    if type(request) is not AudioRequest or type(candidate) is not ReleaseCandidate or type(policy) is not AudioPolicy:
        raise ContractError('AUDIO_BRIDGE_INPUT_TYPE')
    s = request.source
    if (s.candidate_digest, s.run_id, s.revision) != (candidate.content_digest, candidate.run_id, candidate.revision):
        raise ContractError('AUDIO_CANDIDATE_BINDING_MISMATCH')
    idx = {a.artifact_id: a for a in candidate.artifacts}
    refs = all_refs(request)
    if any(idx.get(a.artifact_id) != a for a in refs): raise ContractError('AUDIO_CANDIDATE_ARTIFACT_MISMATCH')
    if {a.artifact_id for a in candidate.artifacts if a.role == 'source'} != {x.artifact.artifact_id for x in s.sources}:
        raise ContractError('AUDIO_CANDIDATE_SOURCE_COVERAGE')
    rp = enterprise_policy() if release_policy is None else release_policy
    if type(rp) is not ReleasePolicy: raise ContractError('AUDIO_RELEASE_POLICY_TYPE')
    result = evaluate(request, artifact_root, policy, as_of=as_of, **options)
    inspected = result.sync.inspected_artifact_ids
    if not inspected: raise ContractError('AUDIO_NO_INSPECTED_ARTIFACTS')
    payload = canonical_bytes(dict(gate='timing_audio_sync', audio_report=result.to_dict(),
                                   actual_media_evaluated=False, product_accepted=False))
    aid = 'qa16-timing-audio-sync-report'
    path = f'qa_audio_reports/{request.content_digest}/timing_audio_sync.json'
    if aid in idx or path in {a.path for a in candidate.artifacts}: raise ContractError('AUDIO_REPORT_COLLISION')
    ref = ArtifactRef(aid, path, hashlib.sha256(payload).hexdigest(), len(payload), 'report')
    status = 'FAIL' if result.status == 'BLOCKED' else 'NOT_RUN'
    codes = tuple(sorted({f.code for area in AREAS for f in getattr(result, area).findings if f.severity != 'INFO'}))[:124] + ('ACTUAL_MEDIA_AUDIO_NOT_EVALUATED', 'UNSIGNED_REVIEW_EVIDENCE')
    gate = GateEvidence('2.0.0', 'qa16-timing-audio-sync', 'timing_audio_sync', candidate.content_digest,
                       rp.content_digest, candidate.run_id, candidate.revision, status, 'bie-qa-audio-v2',
                       '1.0.0', 'review', inspected, ref, as_of,
                       as_of + min(3600, policy.max_receipt_age_seconds, rp.max_evidence_lifetime_seconds), codes, 'UNSIGNED', '')
    return PreparedEvidence(gate, payload)
