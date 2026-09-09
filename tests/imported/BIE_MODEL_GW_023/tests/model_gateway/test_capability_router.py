
import unittest
from bie.model_gateway.capability_router import *
class T(unittest.TestCase):
 def cs(self):return [{"id":"a","capabilities":["text"],"quality":.8,"cost":2},{"id":"b","capabilities":["text","vision"],"quality":.9,"cost":3}]
 def test_cap(self):self.assertEqual(rank(self.cs(),["vision"])[0]["id"],"b")
 def test_quality(self):self.assertEqual(rank(self.cs(),["text"])[0]["id"],"b")
 def test_pref(self):self.assertEqual(rank(self.cs(),["text"],["a"])[0]["id"],"a")
 def test_none(self):
  with self.assertRaises(RoutingError):rank(self.cs(),["audio"])
 def test_disabled(self):
  c=self.cs();c[1]["enabled"]=False
  with self.assertRaises(RoutingError):rank(c,["vision"])
if __name__=="__main__":unittest.main()
