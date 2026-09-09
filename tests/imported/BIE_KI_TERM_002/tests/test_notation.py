import unittest
from bie.knowledge_intelligence.notation import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(register("v","velocity","chapter","p")["meaning"],"velocity")
  self.assertEqual(register("Δ","change","section","p")["symbol"],"Δ")
  with self.assertRaises(E):register("","x","s","p")
  with self.assertRaises(E):register("x","","s","p")
if __name__=='__main__':unittest.main()
