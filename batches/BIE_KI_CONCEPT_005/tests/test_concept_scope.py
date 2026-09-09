import unittest
from knowledge_intelligence.concept_scope import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(assign("c","chapter",["ch1"])["level"],"chapter")
  self.assertEqual(assign("c","section",["s","s"])["containers"],("s",))
  with self.assertRaises(E):assign("c","bad",["x"])
  with self.assertRaises(E):assign("c","chapter",[])
if __name__=='__main__':unittest.main()
