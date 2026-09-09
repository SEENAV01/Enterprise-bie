import unittest
from dataclasses import replace
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.chronology_reasoning import Event,TimeSpan
from bie.reasoning.periodization_reasoning import Period,periodization

class PeriodizationTests(unittest.TestCase):
    def setUp(self):
        self.refs=(EvidenceRef("history:1","primary",.9),);self.p=Period("P1","Early",1,10,("history:1",));self.q=Period("P2","Later",10,20,("history:1",))
    def e(self,lo,hi=None):return Event("E","Event",TimeSpan(lo,lo if hi is None else hi),("history:1",))
    def run_period(self,e,periods=None):return periodization([e],[self.p,self.q] if periods is None else periods,self.refs)
    def test_start_inclusive(self):self.assertEqual(self.run_period(self.e(1)).value["assignments"][0]["definite_period_ids"],["P1"])
    def test_shared_boundary(self):self.assertEqual(self.run_period(self.e(10)).value["assignments"][0]["definite_period_ids"],["P2"])
    def test_end_exclusive(self):self.assertEqual(self.run_period(self.e(20)).value["assignments"][0]["status"],"UNASSIGNED")
    def test_boundary_uncertainty(self):
        r=self.run_period(self.e(9,10));self.assertEqual(r.status,"AMBIGUOUS");self.assertEqual(r.value["assignments"][0]["possible_period_ids"],["P1","P2"]);self.assertEqual(r.value["assignments"][0]["definite_period_ids"],[])
    def test_nested_periods(self):
        child=Period("C","Child",3,5,("history:1",),parent_id="P1");r=self.run_period(self.e(4),[self.p,child]);self.assertEqual(r.value["assignments"][0]["definite_period_ids"],["C","P1"]);self.assertEqual(r.status,"RESOLVED")
    def test_overlap_flagged(self):
        r=self.run_period(self.e(9),[self.p,replace(self.q,start=8)]);self.assertEqual(r.status,"AMBIGUOUS");self.assertEqual(r.value["overlapping_siblings"],[["P1","P2"]])
    def test_different_schemes_preserved(self):
        r=self.run_period(self.e(5),[self.p,replace(self.q,start=1,scheme_id="alternative")]);self.assertEqual(r.value["overlapping_siblings"],[]);self.assertEqual(r.value["assignments"][0]["definite_period_ids"],["P1","P2"])
    def test_gap_no_invention(self):
        r=self.run_period(self.e(11),[self.p,replace(self.q,start=12)]);self.assertEqual(r.value["assignments"][0]["status"],"UNASSIGNED")
    def test_missing_parent(self):
        with self.assertRaises(ValueError):self.run_period(self.e(2),[replace(self.p,parent_id="missing")])
    def test_cyclic_parent(self):
        with self.assertRaises(ValueError):self.run_period(self.e(2),[replace(self.p,parent_id="P1")])
    def test_child_outside_parent(self):
        with self.assertRaises(ValueError):self.run_period(self.e(2),[self.p,replace(self.q,parent_id="P1")])
    def test_reversed_period(self):
        with self.assertRaises(ValueError):self.run_period(self.e(2),[replace(self.p,start=10,end=1)])
    def test_zero_length_period(self):
        with self.assertRaises(ValueError):self.run_period(self.e(2),[replace(self.p,end=1)])
    def test_unknown_event_date(self):
        r=self.run_period(Event("E","Event",TimeSpan(None,None),("history:1",)));self.assertEqual(r.status,"AMBIGUOUS")
    def test_bce_period(self):
        r=self.run_period(self.e(-5),[replace(self.p,start=-10,end=1)]);self.assertEqual(r.value["assignments"][0]["definite_period_ids"],["P1"])
    def test_permutation_identity(self):self.assertEqual(self.run_period(self.e(2)).result_id,self.run_period(self.e(2),[self.q,self.p]).result_id)
