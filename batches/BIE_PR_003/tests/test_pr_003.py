import unittest
from app.bie.prerequisite_intelligence.implicit_prerequisites import *
class T(unittest.TestCase):
 def test_rank(self):
  r=infer_implicit_prerequisites("b",["vector","force"],{"a":["vector","force"],"c":["force"]})
  self.assertEqual([x.prerequisite_id for x in r],["a","c"]); self.assertEqual(r[0].confidence,1)
 def test_casefold(self): self.assertEqual(len(infer_implicit_prerequisites("b",["Force"],{"a":["force"]})),1)
 def test_self_excluded(self): self.assertEqual(infer_implicit_prerequisites("a",["x"],{"a":["x"]}),[])
 def test_threshold(self): self.assertEqual(infer_implicit_prerequisites("b",["x","y"],{"a":["x"]},2),[])
if __name__=="__main__": unittest.main()
