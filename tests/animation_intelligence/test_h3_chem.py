import unittest,hashlib
from bie.animation_intelligence.chemistry_animation_grammar import *
class T(unittest.TestCase):
 def s(self,i,f,c=1,charge=None):return Species(i,f,c,("src",),("r",),charge=charge)
 def test_unbalanced(self):self.assertEqual(plan_reaction("r",[self.s("h2","H2"),self.s("o2","O2")],[self.s("h2o","H2O",2)]).status,"BLOCKED")
 def test_balanced(self):self.assertEqual(plan_reaction("r",[self.s("h2","H2",2),self.s("o2","O2")],[self.s("h2o","H2O",2)]).status,"PASS")
 def test_atom_guard(self):self.assertIn("atom_conservation_failed",plan_reaction("r",[self.s("a","H2")],[self.s("b","H")]).blockers)
 def test_model_guard(self):self.assertEqual(plan_reaction("r",[self.s("a","H2")],[self.s("b","H2")],model_generated=True).status,"BLOCKED")
 def test_model_bound(self):self.assertNotEqual(plan_reaction("r",[self.s("a","H2")],[self.s("b","H2")],model_generated=True,model_fingerprint=hashlib.sha256(b"m").hexdigest()).status,"BLOCKED")
 def test_lineage(self):
  with self.assertRaises(ChemistryAnimationError):plan_reaction("r",[Species("a","H2",1,(),("r",))],[self.s("b","H2")])
 def test_charge(self):self.assertEqual(plan_reaction("r",[self.s("a","Na",1,1)],[self.s("b","Na",1,0)]).status,"BLOCKED")
 def test_not_accepted(self):self.assertFalse(plan_reaction("r",[self.s("a","H2")],[self.s("b","H2")]).accepted)
