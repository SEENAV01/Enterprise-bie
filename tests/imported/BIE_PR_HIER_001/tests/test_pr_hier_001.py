import unittest
from app.bie.prerequisite_intelligence.hierarchical_context import *
class T(unittest.TestCase):
 def test_nearest(self):
  r=resolve_context({"vectors"},[ContextLayer("book",frozenset({"vectors"}),4),ContextLayer("section",frozenset({"vectors"}),1)])
  self.assertEqual(r[0].found_in,"section")
 def test_missing(self): self.assertIsNone(resolve_context({"x"},[])[0].found_in)
 def test_sorted(self): self.assertEqual([x.prerequisite for x in resolve_context({"b","a"},[])],["a","b"])
 def test_distance(self): self.assertEqual(resolve_context({"x"},[ContextLayer("chapter",frozenset({"x"}),2)])[0].distance,2)
if __name__=="__main__": unittest.main()
