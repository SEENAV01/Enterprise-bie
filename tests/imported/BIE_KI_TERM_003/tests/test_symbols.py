import unittest
from bie.knowledge_intelligence.symbols import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(bind("g","gravity","constant","p")["kind"],"constant")
  self.assertEqual(bind("N","newton","unit","p")["entity_id"],"newton")
  with self.assertRaises(E):bind("","x","label","p")
  with self.assertRaises(E):bind("x","x","bad","p")
if __name__=='__main__':unittest.main()
