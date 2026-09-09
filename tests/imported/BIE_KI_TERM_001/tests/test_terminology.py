import unittest
from bie.knowledge_intelligence.terminology import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(register("force","c",["p"])["concept_id"],"c")
  self.assertEqual(register("force","c",["p","p"])["anchors"],("p",))
  with self.assertRaises(E):register("","c",["p"])
  with self.assertRaises(E):register("x","c",[])
if __name__=='__main__':unittest.main()
