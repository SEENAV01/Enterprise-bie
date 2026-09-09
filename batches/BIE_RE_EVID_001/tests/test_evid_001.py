import unittest
from app.bie.reasoning.evidence_aggregation import *
class T(unittest.TestCase):
 def test_one(self): self.assertAlmostEqual(aggregate("c",[Evidence("e","c",.8,"p")]).score,.8)
 def test_many(self): self.assertGreater(aggregate("c",[Evidence("a","c",.5,"p"),Evidence("b","c",.5,"q")]).score,.5)
 def test_ids(self): self.assertEqual(aggregate("c",[Evidence("b","c",.5,"p"),Evidence("a","c",.5,"q")]).evidence_ids,("a","b"))
 def test_empty(self):
  with self.assertRaises(ValueError):aggregate("c",[])
if __name__=="__main__":unittest.main()
