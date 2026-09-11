from dataclasses import dataclass

@dataclass(frozen=True)
class TemporalFixture:
    fixture_id: str
    source_excerpt_id: str
    query: str
    expected_status: str
    required_evidence_ids: tuple[str,...]

@dataclass(frozen=True)
class FixtureOutcome:
    fixture_id: str
    passed: bool
    reasons: tuple[str,...]

def evaluate_fixture(fixture, actual_status, actual_evidence_ids):
    reasons=[]
    if actual_status != fixture.expected_status:
        reasons.append("status_mismatch")
    missing=sorted(set(fixture.required_evidence_ids)-set(actual_evidence_ids))
    if missing:
        reasons.append("missing_required_evidence:"+",".join(missing))
    return FixtureOutcome(fixture.fixture_id,not reasons,tuple(reasons))

def summarize_fixture_outcomes(outcomes):
    xs=tuple(outcomes)
    passed=sum(o.passed for o in xs)
    return {"total":len(xs),"passed":passed,"failed":len(xs)-passed}
