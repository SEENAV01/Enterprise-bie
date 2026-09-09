
import unittest
from bie.model_gateway.capability_taxonomy import *
class T(unittest.TestCase):
 def test_valid(self):self.assertIn("vision",validate_capabilities(["vision"]))
 def test_unknown(self):
  with self.assertRaises(CapabilityError):validate_capabilities(["magic"])
 def test_satisfy(self):self.assertTrue(satisfies(["text","vision"],["vision"]))
 def test_not(self):self.assertFalse(satisfies(["text"],["vision"]))
 def test_empty(self):self.assertTrue(satisfies([],[]))
if __name__=="__main__":unittest.main()
