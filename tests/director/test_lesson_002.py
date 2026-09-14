import unittest
from bie.director.scene_purpose_planning import *
class T(unittest.TestCase):
    def test_map(self): self.assertEqual(plan_scene_purposes([("o","DERIVATION",("e",))])[1].purpose,"DERIVE")
    def test_bookends(self):
        r=plan_scene_purposes([("o","EXPLANATION",("e",))]); self.assertEqual((r[0].purpose,r[-1].purpose),("HOOK","RECAP"))
