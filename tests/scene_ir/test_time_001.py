import unittest
from bie.scene_ir.element_lifetime import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(validate_lifetimes([ElementLifetime("e",0,100)],100),())
 def test_bad_order(self):
  with self.assertRaises(TemporalIRError):ElementLifetime("e",100,50)
 def test_over(self):self.assertEqual(validate_lifetimes([ElementLifetime("e",0,101)],100),("lifetime_exceeds_scene:e",))
 def test_dup(self):
  with self.assertRaises(TemporalIRError):validate_lifetimes([ElementLifetime("e",0,10),ElementLifetime("e",10,20)],20)
 def test_policy(self):
  with self.assertRaises(TemporalIRError):ElementLifetime("e",0,10,"blink")
