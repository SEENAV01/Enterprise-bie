
import unittest
from enterprise.release_api import *
class E:
 def __init__(self,p=True):self.p=p
 def evaluate(self,r):return {"passed":self.p,"gate_results":{"render":self.p}}
class M:
 def __init__(self):self.x={}
 def create(self,r,e):self.x[r]={"run_id":r,"status":"SUCCESS","evidence":e};return self.x[r]
 def get(self,r):return self.x.get(r)
class T(unittest.TestCase):
 def test_eval(self):self.assertTrue(ReleaseAPI(E(),M()).evaluate("r")["passed"])
 def test_certify(self):self.assertEqual(ReleaseAPI(E(),M()).certify("r")["status"],"SUCCESS")
 def test_block(self):
  with self.assertRaises(ReleaseAPIError):ReleaseAPI(E(False),M()).certify("r")
 def test_get(self):
  a=ReleaseAPI(E(),M());a.certify("r");self.assertEqual(a.get("r")["run_id"],"r")
 def test_missing(self):
  with self.assertRaises(ReleaseAPIError):ReleaseAPI(E(),M()).get("r")
if __name__=="__main__":unittest.main()
