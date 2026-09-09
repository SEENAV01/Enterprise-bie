import unittest
from app.bie.prerequisite_intelligence.clustering import *
class T(unittest.TestCase):
 def test_shared_dependent(self):
  r=cluster_prerequisites({"a","b","c"},[("a","c"),("b","c")]); self.assertIn(("a","b"),[x.members for x in r])
 def test_isolated(self): self.assertEqual(cluster_prerequisites({"a"},[])[0].members,("a",))
 def test_threshold(self):
  with self.assertRaises(ValueError): cluster_prerequisites({"a"},[],0)
 def test_unknown(self):
  with self.assertRaises(ValueError): cluster_prerequisites({"a"},[("a","b")])
if __name__=="__main__": unittest.main()
