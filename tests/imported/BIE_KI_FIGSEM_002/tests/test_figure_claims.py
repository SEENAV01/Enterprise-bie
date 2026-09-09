import unittest
from figure_claims import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(bind("f","c","ILLUSTRATES","p")["visual_role"],"ILLUSTRATES")
  self.assertEqual(bind("f","c","PLOTS","p")["claim_id"],"c")
  with self.assertRaises(E):bind("","c","PLOTS","p")
  with self.assertRaises(E):bind("f","c","BAD","p")
