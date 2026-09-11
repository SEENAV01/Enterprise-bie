from bie.reasoning.chronology_reasoning import Event,TimeSpan,chronology
from bie.reasoning.temporal_lineage_reasoning import audit_temporal_lineage
from bie.reasoning.decision_contracts import EvidenceRef
def refs(strength=0.9): return [EvidenceRef("src", "supporting", strength, "source")]

def result(strength=.9):
 r=refs(strength); return chronology([Event("a","A",TimeSpan(1,1),("src",)),Event("b","B",TimeSpan(2,2),("src",))],r),r
def test_full():
 x,r=result(); assert audit_temporal_lineage([x],r).value["coverage"]==1
def test_weak():
 x,r=result(.5); assert audit_temporal_lineage([x],r).status=="AMBIGUOUS"
def test_type():
 import unittest
 with unittest.TestCase().assertRaises(ValueError): audit_temporal_lineage([object()],refs())
def test_empty():
 import unittest
 with unittest.TestCase().assertRaises(ValueError): audit_temporal_lineage([],refs())
def test_deterministic():
 x,r=result(); assert audit_temporal_lineage([x],r).result_id==audit_temporal_lineage([x],r).result_id


# Canonical discovery adapter; original assertions are preserved.
from bie.reasoning.temporal_unittest_bridge_014_018 import build_unittest_case
LegacyTemporalFunctionTests = build_unittest_case(__name__)
