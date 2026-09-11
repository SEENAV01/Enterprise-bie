from bie.reasoning.temporal_state_reasoning import StateChange,state_at
from bie.reasoning.decision_contracts import EvidenceRef
def refs(strength=0.9): return [EvidenceRef("src", "supporting", strength, "source")]

def cs(): return [StateChange("x",1,"a",("src",)),StateChange("x",3,"b",("src",))]
def test_before(): assert state_at(cs(),0,refs()).status=="UNREACHABLE"
def test_first(): assert state_at(cs(),2,refs()).value["state"]=="a"
def test_second(): assert state_at(cs(),3,refs()).value["state"]=="b"
def test_conflict(): assert state_at([StateChange("x",1,"a",("src",)),StateChange("x",1,"b",("src",))],1,refs()).status=="CONFLICT"
def test_entities():
 import unittest
 with unittest.TestCase().assertRaises(ValueError): state_at([StateChange("x",1,"a",("src",)),StateChange("y",2,"b",("src",))],2,refs())


# Canonical discovery adapter; original assertions are preserved.
from bie.reasoning.temporal_unittest_bridge_014_018 import build_unittest_case
LegacyTemporalFunctionTests = build_unittest_case(__name__)
