import unittest
from app.bie.prerequisite_intelligence.qa import *
class T(unittest.TestCase):
 def test_pass(self): self.assertTrue(validate_prerequisite_graph({"a","b"},[("a","b",.9)]).passed)
 def test_cycle(self): self.assertFalse(validate_prerequisite_graph({"a","b"},[("a","b",1),("b","a",1)]).passed)
 def test_unknown(self): self.assertFalse(validate_prerequisite_graph({"a"},[("a","b",1)]).passed)
 def test_duplicate_warning(self):
  r=validate_prerequisite_graph({"a","b"},[("a","b",1),("a","b",1)])
  self.assertTrue(r.passed); self.assertEqual(r.issues[0].code,"DUPLICATE_EDGE")
if __name__=="__main__": unittest.main()
