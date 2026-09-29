"""Unsigned release-v2 evidence bridge. Text success is not media success."""
from __future__ import annotations
import hashlib
from ..release_v2.contracts import ArtifactRef, GateEvidence, ReleaseCandidate, ContractError, canonical_bytes
from ..release_v2.policy import ReleasePolicy, enterprise_policy
from ..source_v2.bridge import PreparedEvidence
from .models import SemanticRequest, SemanticPolicy
from .evaluator import evaluate


def prepare_release_evidence(request: SemanticRequest, candidate: ReleaseCandidate,
                             artifact_root, policy: SemanticPolicy, *, as_of: int,
                             release_policy: ReleasePolicy | None = None, **assessment_options) -> PreparedEvidence:
    if type(request) is not SemanticRequest or type(candidate) is not ReleaseCandidate or type(policy) is not SemanticPolicy:
        raise ContractError('INVALID_SEMANTIC_BRIDGE_INPUT')
    s = request.source
    if (s.candidate_digest, s.run_id, s.revision) != (candidate.content_digest, candidate.run_id, candidate.revision):
        raise ContractError('SEMANTIC_CANDIDATE_BINDING_MISMATCH')
    index = {a.artifact_id: a for a in candidate.artifacts}
    refs = [x.artifact for x in s.sources] + [x.artifact for x in s.outputs]
    if any(index.get(a.artifact_id) != a for a in refs): raise ContractError('SEMANTIC_CANDIDATE_ARTIFACT_MISMATCH')
    if {x.artifact.artifact_id for x in s.sources} != {a.artifact_id for a in candidate.artifacts if a.role == 'source'}:
        raise ContractError('SEMANTIC_CANDIDATE_SOURCE_COVERAGE')
    rp = enterprise_policy() if release_policy is None else release_policy
    if type(rp) is not ReleasePolicy: raise ContractError('INVALID_RELEASE_POLICY')
    result = evaluate(request, artifact_root, policy, as_of=as_of, **assessment_options)
    inspected = result.source.provenance.inspected_artifact_ids
    if not inspected: raise ContractError('NO_VERIFIED_SEMANTIC_ARTIFACTS')
    payload = canonical_bytes(dict(text_semantic_result=result.to_dict(),
        actual_media_semantics_evaluated=False, product_accepted=False))
    ref = ArtifactRef('qa-semantic-report', f'qa_semantic_reports/{request.content_digest}/report.json',
        hashlib.sha256(payload).hexdigest(), len(payload), 'report')
    if ref.artifact_id in index or ref.path in {a.path for a in candidate.artifacts}:
        raise ContractError('SEMANTIC_REPORT_COLLISION')
    # The canonical gate requires source + VIDEO + GAME semantics. We inspected
    # source/support bytes only; neither an unsigned nor a signed version of this
    # text-only envelope may pretend to have checked those product surfaces.
    status = 'FAIL' if result.status == 'BLOCKED' else 'NOT_RUN'
    codes = tuple(sorted({f.code for r in (result.factual, result.coverage, result.contradiction)
                          for f in r.findings if f.severity != 'INFO'}))
    codes = codes[:125] + ('ACTUAL_MEDIA_SEMANTICS_NOT_EVALUATED', 'UNSIGNED_REVIEW_EVIDENCE')
    envelope = GateEvidence('2.0.0', 'qa16-semantic-correctness', 'semantic_correctness',
        candidate.content_digest, rp.content_digest, candidate.run_id, candidate.revision,
        status, 'bie-qa-semantic-v2', '1.0.0', 'review', inspected, ref, as_of,
        as_of + min(3600, policy.max_receipt_age_seconds, rp.max_evidence_lifetime_seconds), codes, 'UNSIGNED', '')
    return PreparedEvidence(envelope, payload)
