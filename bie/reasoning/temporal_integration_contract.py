from dataclasses import dataclass

@dataclass(frozen=True)
class TemporalIntegrationPayload:
    result_id: str
    status: str
    conclusion: str | None
    evidence_ids: tuple[str,...]
    requires_review: bool
    axis: str | None = None

def validate_integration_payload(p):
    issues=[]
    if not p.result_id:
        issues.append("missing_result_id")
    if not p.evidence_ids:
        issues.append("missing_evidence")
    if p.status == "RESOLVED" and not p.conclusion:
        issues.append("missing_conclusion")
    if p.status != "RESOLVED" and not p.requires_review:
        issues.append("review_required_for_nonresolved")
    return tuple(issues)

def downstream_safe(p):
    return not validate_integration_payload(p)
