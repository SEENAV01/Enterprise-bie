import unittest
from bie.reasoning.mechanism_path_reasoning import MechanismStep, find_mechanism_paths

class TestMechanismPathReasoning(unittest.TestCase):
    def test_multi_step_path(self):
        p=find_mechanism_paths(["a","b","c"],[
            MechanismStep("a","b","m1",("e1",),.8),
            MechanismStep("b","c","m2",("e2",),.7)
        ],"a","c")
        self.assertEqual(p[0].nodes,("a","b","c"))
        self.assertEqual(p[0].confidence,.7)
        self.assertEqual(p[0].evidence_ids,("e1","e2"))

    def test_cycles_do_not_loop(self):
        p=find_mechanism_paths(["a","b","c"],[
            MechanismStep("a","b","m1",("e1",)),
            MechanismStep("b","a","m2",("e2",)),
            MechanismStep("b","c","m3",("e3",))
        ],"a","c")
        self.assertEqual(len(p),1)

    def test_evidence_required(self):
        with self.assertRaises(ValueError):
            find_mechanism_paths(["a","b"],[MechanismStep("a","b","m",())],"a","b")
