import unittest
from app.bie.readiness_intelligence.readiness_checks import *
class T(unittest.TestCase):
 def test_ready(self): self.assertTrue(check_readiness("c",{"a"},{"a":.9}).ready)
 def test_missing(self): self.assertEqual(check_readiness("c",{"a","b"},{"a":.9}).missing,("b",))
 def test_no_prereq(self): self.assertEqual(check_readiness("c",set(),{}).score,1)
 def test_invalid(self):
  with self.assertRaises(ValueError): check_readiness("c",set(),{},1.2)
if __name__=="__main__": unittest.main()
