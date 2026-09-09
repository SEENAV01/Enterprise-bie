import unittest
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.chronology_reasoning import Event, TimeSpan, year
from bie.reasoning.event_order_reasoning import Before, event_order

class EventOrderTests(unittest.TestCase):
    def setUp(self):self.refs=(EvidenceRef("history:1","primary",.9),)
    def e(self,id,lo=None,hi=None):return Event(id,id,TimeSpan(lo,hi),("history:1",))
    def c(self,a,b):return Before(a,b,("history:1",))
    def run_order(self,events,constraints):return event_order(events,constraints,self.refs)
    def test_unique_chain(self):
        r=self.run_order([self.e(x) for x in "ABC"],[self.c("A","B"),self.c("B","C")]);self.assertEqual(r.value["linear_extension"],["A","B","C"]);self.assertTrue(r.value["unique_order"])
    def test_incomparable_nodes(self):
        r=self.run_order([self.e(x) for x in "ABC"],[self.c("A","C")]);self.assertEqual(r.status,"AMBIGUOUS");self.assertFalse(r.value["unique_order"])
    def test_cycle_witness_excludes_descendant(self):
        r=self.run_order([self.e(x) for x in "ABCD"],[self.c("A","B"),self.c("B","C"),self.c("C","A"),self.c("C","D")]);self.assertEqual(r.status,"CONFLICT");self.assertEqual(r.value["linear_extension"],[]);self.assertNotIn("D",r.value["cycle_witness"]);self.assertEqual(r.value["cycle_witness"][0],r.value["cycle_witness"][-1])
    def test_date_order_derived(self):
        r=self.run_order([self.e("B",2,2),self.e("A",1,1)],[]);self.assertEqual(r.value["linear_extension"],["A","B"]);self.assertEqual(r.value["edges"][0]["kind"],"date_bounds")
    def test_date_constraint_conflict(self):
        r=self.run_order([self.e("A",2,2),self.e("B",1,1)],[self.c("A","B")]);self.assertEqual(r.status,"CONFLICT")
    def test_same_time_strict_order_conflict(self):
        r=self.run_order([self.e("A",1,1),self.e("B",1,1)],[self.c("A","B")]);self.assertEqual(r.status,"CONFLICT")
    def test_chain_interval_infeasibility(self):
        r=self.run_order([self.e(x,1,2) for x in "ABC"],[self.c("A","B"),self.c("B","C")]);self.assertEqual(r.status,"CONFLICT");self.assertTrue(r.value["violations"])
    def test_compatible_uncertain_constraint(self):
        r=self.run_order([self.e("A",1,3),self.e("B",2,5)],[self.c("A","B")]);self.assertEqual(r.status,"RESOLVED")
    def test_dangling_node(self):
        with self.assertRaises(ValueError):self.run_order([self.e("A")],[self.c("A","Z")])
    def test_self_constraint(self):
        with self.assertRaises(ValueError):self.run_order([self.e("A")],[self.c("A","A")])
    def test_duplicate_constraint(self):
        with self.assertRaises(ValueError):self.run_order([self.e("A"),self.e("B")],[self.c("A","B"),self.c("A","B")])
    def test_permutation_identity(self):
        events=[self.e(x) for x in "ABC"];edges=[self.c("A","B"),self.c("B","C")];self.assertEqual(self.run_order(events,edges).result_id,self.run_order(events[::-1],edges[::-1]).result_id)
    def test_iterative_large_chain(self):
        events=[self.e(f"E{i:04}") for i in range(1100)];edges=[self.c(events[i].event_id,events[i+1].event_id) for i in range(1099)]
        self.assertEqual(len(self.run_order(events,edges).value["linear_extension"]),1100)
