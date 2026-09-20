from dataclasses import dataclass
from typing import Mapping, Any

class RealBookHarnessError(ValueError): pass

@dataclass(frozen=True)
class RealBookFixture:
    fixture_id:str
    domain:str
    source_kind:str
    source_locator:str
    rights_basis:str
    excerpt_hash:str
    independent_expected:bool
    expected_actions:tuple[str,...]
    expected_blockers:tuple[str,...]=()
    metadata:Mapping[str,Any]|None=None

@dataclass(frozen=True)
class RealBookCaseResult:
    fixture_id:str
    status:str
    action_recall:float
    unexpected_actions:tuple[str,...]
    missing_actions:tuple[str,...]
    blocker_match:bool
    evidence_complete:bool
    empirical_render_status:str="NOT_RUN"
    review_required:bool=True
    accepted:bool=False

def validate_fixture(f):
    if f.source_kind!="REAL_BOOK":
        raise RealBookHarnessError("fixture is not marked REAL_BOOK")
    if not f.fixture_id or not f.domain or not f.source_locator or not f.rights_basis or len(f.excerpt_hash)!=64:
        raise RealBookHarnessError("fixture provenance incomplete")
    if not f.independent_expected:
        raise RealBookHarnessError("expected decisions must be independently authored")
    if not f.expected_actions:
        raise RealBookHarnessError("expected_actions required")
    return True

def evaluate_realbook_case(fixture, predicted_actions, predicted_blockers=(), *,
                           evidence_complete=True, empirical_render_status="NOT_RUN"):
    validate_fixture(fixture)
    pred=tuple(predicted_actions); expected=set(fixture.expected_actions)
    got=set(pred)
    missing=tuple(sorted(expected-got));unexpected=tuple(sorted(got-expected))
    recall=(len(expected)-len(missing))/len(expected)
    blocker_match=set(predicted_blockers)==set(fixture.expected_blockers)
    status="PASS" if recall==1 and not unexpected and blocker_match and evidence_complete else "BLOCKED"
    return RealBookCaseResult(
        fixture.fixture_id,status,round(recall,6),unexpected,missing,blocker_match,
        bool(evidence_complete),empirical_render_status,True,False
    )

def section_realbook_status(results):
    results=tuple(results)
    if not results:return "NOT_RUN"
    if any(r.status!="PASS" for r in results):return "BLOCKED"
    domains={r.fixture_id.split(":",1)[0] for r in results}
    return "PASS" if len(domains)>=3 else "REVIEW"
