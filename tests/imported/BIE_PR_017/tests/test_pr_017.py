import unittest
from app.bie.prerequisite_intelligence.mastery import *
class T(unittest.TestCase):
 def test_ready(self): self.assertTrue(evaluate_mastery("c",{"a"},{"a":.8}).ready)
 def test_block(self): self.assertEqual(evaluate_mastery("c",{"a"},{"a":.2}).blocking,("a",))
 def test_no_prereq(self): self.assertEqual(evaluate_mastery("c",set(),{}).readiness,1)
 def test_threshold(self):
  with self.assertRaises(ValueError): evaluate_mastery("c",set(),{},2)
if __name__=="__main__": unittest.main()
