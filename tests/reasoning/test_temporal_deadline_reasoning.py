from bie.reasoning.chronology_reasoning import TimeSpan
from bie.reasoning.temporal_deadline_reasoning import deadline_status
from bie.reasoning.decision_contracts import EvidenceRef
def refs(strength=0.9): return [EvidenceRef("src", "supporting", strength, "source")]

def test_ontime(): assert deadline_status(TimeSpan(1,3),TimeSpan(3,3),refs()).value["classification"]=="ON_TIME"
def test_late(): assert deadline_status(TimeSpan(4,5),TimeSpan(3,3),refs()).value["classification"]=="LATE"
def test_ambiguous(): assert deadline_status(TimeSpan(2,4),TimeSpan(3,3),refs()).status=="AMBIGUOUS"
def test_deadline_point():
 import unittest
 with unittest.TestCase().assertRaises(ValueError): deadline_status(TimeSpan(1,2),TimeSpan(2,3),refs())
def test_axis():
 import unittest
 with unittest.TestCase().assertRaises(ValueError): deadline_status(TimeSpan(1,2),TimeSpan(2,2,"gregorian_day"),refs())


# Canonical discovery adapter; original assertions are preserved.
from bie.reasoning.temporal_unittest_bridge_014_018 import build_unittest_case
LegacyTemporalFunctionTests = build_unittest_case(__name__)
