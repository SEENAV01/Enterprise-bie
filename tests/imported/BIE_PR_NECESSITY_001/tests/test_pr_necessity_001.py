import unittest
from bie.prerequisite_intelligence.necessity import *
class T(unittest.TestCase):
 def test_necessary(self): self.assertTrue(test_necessity("vectors",1,1,1).necessary)
 def test_not(self): self.assertFalse(test_necessity("history",.1,0,0).necessary)
 def test_reason(self): self.assertIn("direct_dependency",test_necessity("x",1,0,0).reasons)
 def test_invalid(self):
  with self.assertRaises(ValueError): test_necessity("x",2,0,0)
if __name__=="__main__": unittest.main()
