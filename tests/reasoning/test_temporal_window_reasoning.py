from bie.reasoning.chronology_reasoning import TimeSpan
from bie.reasoning.temporal_window_reasoning import intersect_windows
from bie.reasoning.decision_contracts import EvidenceRef
def refs(strength=0.9): return [EvidenceRef("src", "supporting", strength, "source")]

def test_point(): assert intersect_windows([TimeSpan(1,3),TimeSpan(2,2)],refs()).status=="RESOLVED"
def test_range(): assert intersect_windows([TimeSpan(1,5),TimeSpan(2,4)],refs()).status=="AMBIGUOUS"
def test_conflict(): assert intersect_windows([TimeSpan(1,2),TimeSpan(3,4)],refs()).status=="CONFLICT"
def test_axis():
 import unittest
 with unittest.TestCase().assertRaises(ValueError): intersect_windows([TimeSpan(1,2),TimeSpan(1,2,"gregorian_day")],refs())
def test_empty():
 import unittest
 with unittest.TestCase().assertRaises(ValueError): intersect_windows([],refs())


# Canonical discovery adapter; original assertions are preserved.
from bie.reasoning.temporal_unittest_bridge_014_018 import build_unittest_case
LegacyTemporalFunctionTests = build_unittest_case(__name__)
