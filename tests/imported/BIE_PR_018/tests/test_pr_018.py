import unittest
from bie.prerequisite_intelligence.bridge_requirement import *
class T(unittest.TestCase):
 def test_required(self): self.assertTrue(bridge_requirement({"a"},set()).required)
 def test_not_missing(self): self.assertFalse(bridge_requirement({"a"},{"a"}).required)
 def test_low_risk(self): self.assertFalse(bridge_requirement({"a"},set(),{"a":.2}).required)
 def test_max_risk(self): self.assertEqual(bridge_requirement({"a","b"},set(),{"a":.2,"b":.9}).risk,.9)
if __name__=="__main__": unittest.main()
