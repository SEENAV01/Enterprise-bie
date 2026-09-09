import unittest
from app.bie.prerequisite_intelligence.candidate_edges import *
class T(unittest.TestCase):
 def test_explicit_and_inferred(self):
  cs=[Concept("charge",0,frozenset({"charge"})),Concept("coulomb",1,frozenset({"charge","force"}),frozenset({"charge"}))]
  es=generate_candidate_edges(cs)
  self.assertEqual(es[0].prerequisite_id,"charge"); self.assertEqual(es[0].score,1.0)
 def test_no_backward_or_self(self):
  cs=[Concept("a",0,frozenset({"x"})),Concept("b",1,frozenset({"x"}))]
  self.assertTrue(all(e.prerequisite_id=="a" for e in generate_candidate_edges(cs,threshold=0)))
 def test_duplicate_ids(self):
  with self.assertRaises(ValueError): generate_candidate_edges([Concept("a",0),Concept("a",1)])
 def test_unknown_explicit_ignored(self):
  self.assertEqual(generate_candidate_edges([Concept("a",0)],{"a":["missing"]}),[])
if __name__=="__main__": unittest.main()
