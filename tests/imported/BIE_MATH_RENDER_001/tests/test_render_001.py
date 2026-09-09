import unittest
from bie.math_intelligence.math_scene_contract import *
class T(unittest.TestCase):
 def test_morph(self): self.assertEqual(cue("equation_morph","a=b","b=a",reason="symmetry").after,"b=a")
 def test_highlight(self): self.assertEqual(cue("highlight_term","F=ma",targets=("a",),reason="focus variable").targets,("a",))
 def test_after(self):
  with self.assertRaises(ValueError):cue("substitute","x=y",reason="replace y")
 def test_unknown(self):
  with self.assertRaises(ValueError):cue("spin","x",reason="x")
if __name__=="__main__":unittest.main()
