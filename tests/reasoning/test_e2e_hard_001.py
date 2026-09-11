import unittest
from bie.reasoning.reasoning_realbook_fixture import SourceAnchor,RealBookReasoningFixture,evaluate_realbook_fixture
from bie.reasoning.reasoning_integration_gate import ReasoningStageEvidence
from bie.reasoning.cross_family_arbitration import FamilyConstraint

class TestRealBookFixture(unittest.TestCase):
    def fixture(self,eid="e1"):
        stages=[
          ReasoningStageEvidence("evidence","src"),
          ReasoningStageEvidence("decision","d",(eid,),("src",)),
          ReasoningStageEvidence("graph","g",(eid,),("d",)),
          ReasoningStageEvidence("uncertainty","u",(eid,),("d",)),
          ReasoningStageEvidence("qa","q",(eid,),("d","g","u"))]
        cs=[FamilyConstraint("temporal","p","SUPPORTS","RESOLVED",(eid,),.9),
            FamilyConstraint("causal","p","SUPPORTS","RESOLVED",(eid,),.8)]
        return RealBookReasoningFixture("fx",(SourceAnchor("e1",12,"source text"),),tuple(stages),tuple(cs))
    def test_grounded_fixture_passes(self):
        self.assertTrue(evaluate_realbook_fixture(self.fixture()).passed)
    def test_missing_source_anchor_blocks(self):
        r=evaluate_realbook_fixture(self.fixture("missing"))
        self.assertEqual(r.missing_anchor_evidence_ids,("missing",)); self.assertFalse(r.passed)
    def test_conflict_blocks(self):
        f=self.fixture()
        cs=(f.constraints[0],FamilyConstraint("causal","p","OPPOSES","RESOLVED",("e1",),.8))
        f=RealBookReasoningFixture(f.fixture_id,f.anchors,f.stage_artifacts,cs)
        self.assertFalse(evaluate_realbook_fixture(f).passed)
