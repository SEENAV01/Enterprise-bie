from bie.reasoning.chronology_reasoning import Event,TimeSpan
from bie.reasoning.event_order_reasoning import Before
from bie.reasoning.periodization_reasoning import Period
from bie.reasoning.temporal_reasoning_engine import temporal_reasoning_engine
from bie.reasoning.decision_contracts import EvidenceRef
def refs(strength=0.9): return [EvidenceRef("src", "supporting", strength, "source")]

def data():
 e=[Event("a","A",TimeSpan(1,1),("src",)),Event("b","B",TimeSpan(2,2),("src",))]; c=[Before("a","b",("src",))]; p=[Period("p","P",1,3,("src",))]; return e,c,p
def test_resolved():
 e,c,p=data(); assert temporal_reasoning_engine(e,c,p,refs()).status=="RESOLVED"
def test_ids():
 e,c,p=data(); assert temporal_reasoning_engine(e,c,p,refs()).value["synthesis_result_id"].startswith("reasoning.inference")
def test_deterministic():
 e,c,p=data(); assert temporal_reasoning_engine(e,c,p,refs()).result_id==temporal_reasoning_engine(e,c,p,refs()).result_id
def test_low_conf_review():
 e,c,p=data(); assert temporal_reasoning_engine(e,c,p,refs(.5)).status=="AMBIGUOUS"
def test_conflict_preserved():
 e,c,p=data(); c.append(Before("b","a",("src",))); assert temporal_reasoning_engine(e,c,p,refs()).status=="CONFLICT"


# Canonical discovery adapter; original assertions are preserved.
from bie.reasoning.temporal_unittest_bridge_014_018 import build_unittest_case
LegacyTemporalFunctionTests = build_unittest_case(__name__)
