
import unittest
from bie.infrastructure.compatibility_matrix import *
class T(unittest.TestCase):
 def setUp(self): self.m=CompatibilityMatrix([CompatibilityRule("api",1,3),CompatibilityRule("worker",2,4)])
 def test_true(self): self.assertTrue(self.m.check("api",2))
 def test_false(self): self.assertFalse(self.m.check("api",4))
 def test_assert(self):
  with self.assertRaises(CompatibilityError): self.m.assert_compatible("api",4)
 def test_unknown(self):
  with self.assertRaises(CompatibilityError): self.m.check("x",1)
 def test_common(self): self.assertEqual(self.m.common_versions(["api","worker"]),[2,3])
 def test_no_common(self):
  m=CompatibilityMatrix([CompatibilityRule("a",1,1),CompatibilityRule("b",2,2)]);self.assertEqual(m.common_versions(["a","b"]),[])
if __name__=="__main__": unittest.main()
