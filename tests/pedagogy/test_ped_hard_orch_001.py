import unittest
from bie.pedagogy.pedagogy_plan_contract import PedagogyDecision,build_pedagogy_plan

class TestPedagogyPlanContract(unittest.TestCase):
    def test_plan_is_deterministic(self):
        d1=PedagogyDecision("d1","objective","o1",("e1",))
        d2=PedagogyDecision("d2","sequence","l1",("e1",),("d1",))
        a=build_pedagogy_plan(plan_id="p",source_id="s",objective_ids=["o2","o1"],lesson_ids=["l1"],decisions=[d2,d1],policy_version="v1")
        b=build_pedagogy_plan(plan_id="p",source_id="s",objective_ids=["o1","o2"],lesson_ids=["l1"],decisions=[d1,d2],policy_version="v1")
        self.assertEqual(a.fingerprint(),b.fingerprint())

    def test_nonresolved_requires_review(self):
        with self.assertRaises(ValueError):
            build_pedagogy_plan(plan_id="p",source_id="s",objective_ids=["o"],lesson_ids=["l"],
                decisions=[PedagogyDecision("d","x","p",("e",),status="AMBIGUOUS")],policy_version="v1")

    def test_unknown_parent_rejected(self):
        with self.assertRaises(ValueError):
            build_pedagogy_plan(plan_id="p",source_id="s",objective_ids=["o"],lesson_ids=["l"],
                decisions=[PedagogyDecision("d","x","p",("e",),("missing",))],policy_version="v1")
