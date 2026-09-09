import unittest
from bie.knowledge_intelligence.concept_aliases import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(bind("Electric field",["E-field","electric field"," E-field "])["aliases"],("E-field",))
  self.assertEqual(bind("Force",[])["aliases"],())
  with self.assertRaises(E):bind("",["x"])
  self.assertEqual(bind("A",[" ","B"])["aliases"],("B",))
if __name__=='__main__':unittest.main()
