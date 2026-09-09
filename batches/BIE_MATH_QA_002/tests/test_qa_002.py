import unittest
from app.bie.math_intelligence.derivation_qa import *
class T(unittest.TestCase):
 def test_pass(self): self.assertEqual(assess(3,3,True,True).score,1)
 def test_step(self): self.assertIn("invalid_steps",assess(3,2,True,True).failures)
 def test_chain(self): self.assertFalse(assess(2,2,False,True).passed)
 def test_bad(self):
  with self.assertRaises(ValueError):assess(0,0,True,True)
if __name__=="__main__":unittest.main()
