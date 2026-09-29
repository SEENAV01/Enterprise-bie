"""Read-only, fail-closed release-evidence aggregation; no SUCCESS certification."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .artifacts import ArtifactCheck, ArtifactStore
from .contracts import (ArtifactRef, ContractError, EvidenceBundle, VERSION, canonical_bytes, integer)
from .policy import ReleasePolicy, enterprise_policy
from .trust import DenyAllVerifier, EvidenceVerifier, TrustResult
from .diagnostics import legacy_blockers


@dataclass(frozen=True, slots=True)
class EvidenceCheck:
    evidence_id: str
    evaluator_id: str
    status: str
    diagnostics: tuple[str, ...]
    assurance: str
    report_sha256: str
    principal_id: str = ""
    independence_group: str = ""
    credential_fingerprint: str = ""
    trust_expires_at: int = 0


@dataclass(frozen=True, slots=True)
class GateResult:
    gate_id: str
    owner: str
    status: str
    diagnostics: tuple[str, ...]
    evidence: tuple[EvidenceCheck, ...]


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    schema_version: str
    evaluator_version: str
    bundle_digest: str
    candidate_digest: str
    policy_digest: str
    as_of: int
    release_status: str
    ready_for_review: bool
    release_authorized: bool
    product_accepted: bool
    blocking_gates: tuple[str, ...]
    global_diagnostics: tuple[str, ...]
    gate_results: tuple[GateResult, ...]
    artifact_checks: tuple[ArtifactCheck, ...]
    certification_boundary: str = "BIE-QA-REL-004_NOT_IMPLEMENTED_IN_THIS_BATCH"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_bytes(self) -> bytes:
        return canonical_bytes(self.to_dict())


class ReleaseEvaluator:
    def __init__(self, policy: ReleasePolicy | None = None,
                 verifier: EvidenceVerifier | None = None) -> None:
        self.policy = enterprise_policy() if policy is None else policy
        if type(self.policy) is not ReleasePolicy:
            raise ContractError("INVALID_POLICY_TYPE")
        self.verifier = DenyAllVerifier() if verifier is None else verifier

    def evaluate(self, bundle: EvidenceBundle, artifact_root: str | Path,
                 *, as_of: int) -> EvaluationReport:
        if type(bundle) is not EvidenceBundle:
            raise ContractError("INVALID_BUNDLE_TYPE")
        integer(as_of, "as_of")
        rules = {g.gate_id: g for g in self.policy.gates}
        by_gate: dict[str, list] = {gid: [] for gid in rules}
        global_codes: set[str] = set()
        artifact_checks: dict[ArtifactRef, ArtifactCheck] = {}
        candidate = bundle.candidate
        candidate_digest = candidate.content_digest
        policy_digest = self.policy.content_digest
        subjects = {a.artifact_id: a for a in candidate.artifacts}
        store = ArtifactStore(artifact_root)
        available = False
        try:
            store.__enter__()
            available = True
        except ContractError as exc:
            global_codes.add(exc.code)

        def check(reference: ArtifactRef) -> ArtifactCheck:
            if reference not in artifact_checks:
                if available:
                    artifact_checks[reference] = store.check(reference)
                else:
                    artifact_checks[reference] = ArtifactCheck(reference.artifact_id, reference.path,
                        "ERROR", "ARTIFACT_STORE_UNAVAILABLE", reference.sha256)
            return artifact_checks[reference]

        try:
            for artifact in sorted(candidate.artifacts, key=lambda a: a.artifact_id):
                if check(artifact).status != "PASS":
                    global_codes.add("CANDIDATE_ARTIFACT_INVALID")
            for evidence in sorted(bundle.evidence, key=lambda e: e.evidence_id):
                rule = rules.get(evidence.gate_id)
                if rule is None:
                    global_codes.add("UNKNOWN_EVIDENCE_GATE")
                    continue
                codes: set[str] = set()
                if evidence.candidate_digest != candidate_digest:
                    codes.add("CANDIDATE_BINDING_MISMATCH")
                if evidence.policy_digest != policy_digest:
                    codes.add("POLICY_BINDING_MISMATCH")
                if evidence.run_id != candidate.run_id:
                    codes.add("RUN_BINDING_MISMATCH")
                if evidence.revision != candidate.revision:
                    codes.add("REVISION_BINDING_MISMATCH")
                if evidence.created_at > as_of:
                    codes.add("FUTURE_EVIDENCE")
                if evidence.expires_at <= as_of:
                    codes.add("EXPIRED_EVIDENCE")
                if evidence.expires_at - evidence.created_at > self.policy.max_evidence_lifetime_seconds:
                    codes.add("EVIDENCE_LIFETIME_EXCEEDED")
                if evidence.kind not in rule.allowed_kinds:
                    codes.add("UNSUPPORTED_PROOF_KIND")
                inspected = set(evidence.inspected_artifact_ids)
                if not inspected.issubset(subjects):
                    codes.add("UNKNOWN_INSPECTED_ARTIFACT")
                needed = {a.artifact_id for a in candidate.artifacts if a.role in rule.required_roles}
                if not set(rule.required_roles).issubset({a.role for a in candidate.artifacts}) or not needed.issubset(inspected):
                    codes.add("INCOMPLETE_ARTIFACT_COVERAGE")
                if any(check(subjects[aid]).status != "PASS" for aid in sorted(inspected.intersection(subjects))):
                    codes.add("INSPECTED_ARTIFACT_INVALID")
                report_check = check(evidence.report)
                if report_check.status != "PASS":
                    codes.add(report_check.diagnostic)
                try:
                    # All current readiness paths require an explicit verification
                    # clock. Old plugins need an out-of-band migration, not fallback.
                    if not callable(getattr(self.verifier,'verify_at',None)):
                        raise ContractError('TRUST_CLOCK_INTERFACE_REQUIRED')
                    trust = self.verifier.verify_at(evidence,as_of=as_of)
                    if type(trust) is not TrustResult:
                        raise ContractError("INVALID_TRUST_RESULT")
                except Exception:
                    # A failing verifier cannot accidentally grant release authority.
                    trust = TrustResult(False, "TRUST_VERIFIER_ERROR", "none")
                if not trust.accepted:
                    codes.add(trust.diagnostic)
                if trust.accepted and (not trust.principal_id or not trust.independence_group or
                                       not trust.credential_fingerprint or trust.valid_until<=as_of):
                    codes.add('UNVERIFIED_PRINCIPAL_IDENTITY')
                invalid_evidence=bool(codes)
                for diagnostic in legacy_blockers(evidence.diagnostics):
                    codes.add(diagnostic.code)
                if evidence.diagnostics:
                    codes.add('BLOCKING_EVIDENCE_DIAGNOSTIC')
                if evidence.status != "PASS":
                    codes.add(f"EVIDENCE_{evidence.status}")
                status = "PASS" if not codes else (
                    "FAIL" if not invalid_evidence and evidence.status in ("PASS","FAIL") else "ERROR")
                by_gate[evidence.gate_id].append(EvidenceCheck(
                    evidence.evidence_id, evidence.evaluator_id, status, tuple(sorted(codes)),
                    trust.assurance, evidence.report.sha256,trust.principal_id,trust.independence_group,
                    trust.credential_fingerprint,trust.valid_until))
        finally:
            store.__exit__()

        gate_results = []
        for rule in sorted(self.policy.gates, key=lambda g: g.gate_id):
            records = tuple(by_gate[rule.gate_id])
            reasons: set[str] = set()
            if not records:
                status = "PENDING"
                reasons.add("MISSING_REQUIRED_EVIDENCE")
            elif any(record.status == "ERROR" for record in records):
                status = "ERROR"
                reasons.add("INVALID_EVIDENCE")
            elif any(record.status == "FAIL" for record in records):
                status = "FAIL"
                reasons.add("FAILED_EVIDENCE")
            else:
                status = "PASS"
                if len({record.evaluator_id for record in records}) < rule.min_distinct_evaluators:
                    status = "ERROR"
                    reasons.add("INSUFFICIENT_DISTINCT_EVALUATORS")
                independent=min(len({r.principal_id for r in records}),
                                len({r.independence_group for r in records}),
                                len({r.credential_fingerprint for r in records}))
                if independent<rule.min_distinct_evaluators:
                    status='ERROR'
                    reasons.add('INSUFFICIENT_INDEPENDENT_EVALUATORS')
                if len({record.report_sha256 for record in records}) < rule.min_distinct_evaluators:
                    status = "ERROR"
                    reasons.add("INSUFFICIENT_DISTINCT_REPORTS")
            gate_results.append(GateResult(rule.gate_id, rule.owner, status, tuple(sorted(reasons)), records))
        blockers = tuple(gate.gate_id for gate in gate_results if gate.status != "PASS")
        if blockers or global_codes:
            release_status = "BLOCKED"
        elif any(record.assurance != "operator_managed" for gate in gate_results for record in gate.evidence):
            release_status = "CONTRACT_ONLY"
            global_codes.add("NON_PRODUCTION_TRUST")
        else:
            release_status = "READY_FOR_REVIEW"
        return EvaluationReport(
            VERSION, VERSION, bundle.content_digest, candidate_digest, policy_digest, as_of,
            release_status, release_status == "READY_FOR_REVIEW", False, False,
            blockers, tuple(sorted(global_codes)), tuple(gate_results),
            tuple(sorted(artifact_checks.values(), key=lambda a: (a.artifact_id, a.path))))
