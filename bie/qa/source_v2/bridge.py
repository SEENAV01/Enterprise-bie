"""Opt-in evidence bridge to preserved Section16 Batch001 release_v2.

Reports are recomputed, never accepted as caller-declared success. The bridge
returns unsigned envelopes and exact report bytes. It neither writes artifacts
nor configures trust, signs evidence, runs media checks, or authorizes release.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from ..release_v2.contracts import (ArtifactRef, ReleaseCandidate, GateEvidence, ContractError,
                                    VERSION as RELEASE_VERSION, canonical_bytes)
from ..release_v2.policy import enterprise_policy, ReleasePolicy
from .models import Request, Policy
from .attestation import Assessment, AssessmentVerifier
from .evaluator import evaluate


@dataclass(frozen=True, slots=True)
class PreparedEvidence:
    envelope: GateEvidence
    report_bytes: bytes


def prepare_release_evidence(request: Request, candidate: ReleaseCandidate,
                             artifact_root, policy: Policy, *, as_of: int,
                             assessments: tuple[Assessment, ...] = (),
                             verifier: AssessmentVerifier | None = None,
                             release_policy: ReleasePolicy | None = None) -> tuple[PreparedEvidence, ...]:
    if type(request) is not Request or type(candidate) is not ReleaseCandidate:
        raise ContractError('INVALID_RELEASE_BRIDGE_INPUT')
    if (request.candidate_digest != candidate.content_digest or request.run_id != candidate.run_id or
            request.revision != candidate.revision):
        raise ContractError('SOURCE_CANDIDATE_BINDING_MISMATCH')
    index = {a.artifact_id: a for a in candidate.artifacts}
    refs = [s.artifact for s in request.sources] + [o.artifact for o in request.outputs]
    if any(index.get(ref.artifact_id) != ref for ref in refs):
        raise ContractError('SOURCE_CANDIDATE_ARTIFACT_MISMATCH')
    if {s.artifact.artifact_id for s in request.sources} != {a.artifact_id for a in candidate.artifacts if a.role == 'source'}:
        raise ContractError('SOURCE_CANDIDATE_COVERAGE_MISMATCH')
    release_policy = enterprise_policy() if release_policy is None else release_policy
    if type(release_policy) is not ReleasePolicy:
        raise ContractError('INVALID_RELEASE_POLICY')
    pair = evaluate(request, artifact_root, policy, assessments=assessments, verifier=verifier, as_of=as_of)
    prepared = []
    for gate, report in (('source_grounding', pair.grounding), ('citation_provenance', pair.provenance)):
        payload = canonical_bytes(report.to_dict())
        report_ref = ArtifactRef(f'qa-source-{gate}',
            f'qa_source_reports/{request.content_digest}/{gate}.json',
            hashlib.sha256(payload).hexdigest(), len(payload), 'report')
        if report_ref.artifact_id in index or report_ref.path in {a.path for a in candidate.artifacts}:
            raise ContractError('SOURCE_REPORT_ARTIFACT_COLLISION')
        status = {'CHECKS_PASSED': 'PASS', 'BLOCKED': 'FAIL', 'REVIEW_REQUIRED': 'NOT_RUN'}[report.status]
        codes = tuple(sorted({f.code for f in report.findings if f.severity != 'INFO'}))
        if len(codes) > 127:
            codes = codes[:127] + ('ADDITIONAL_FINDINGS_IN_REPORT',)
        if status != 'PASS' and not codes: codes = ('SOURCE_REVIEW_REQUIRED',)
        # Both source gates require inspected source IDs. A total I/O failure
        # cannot generate an envelope pretending any artifact was inspected.
        if not report.inspected_artifact_ids:
            raise ContractError('NO_VERIFIED_SOURCE_ARTIFACTS')
        envelope = GateEvidence(RELEASE_VERSION, f'qa16-{gate}', gate,
            candidate.content_digest, release_policy.content_digest, request.run_id, request.revision,
            status, 'bie-qa-source-v2', '1.0.0', 'review', report.inspected_artifact_ids,
            report_ref, as_of, as_of + min(3600, policy.max_receipt_age_seconds), codes, 'UNSIGNED', '')
        prepared.append(PreparedEvidence(envelope, payload))
    return tuple(prepared)
