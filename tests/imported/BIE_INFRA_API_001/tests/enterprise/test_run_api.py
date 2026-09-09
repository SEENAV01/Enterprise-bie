
import unittest
from bie.infrastructure.run_api import *
class S:
 def __init__(self):self.x={}
 def create(self,r):
  v=RunView("r1","CREATED",r.source_ref,r.config_hash);self.x[v.run_id]=v;return v
 def get(self,k):return self.x.get(k)
 def list(self):return self.x.values()
class T(unittest.TestCase):
 def test_create(self):self.assertEqual(RunAPI(S()).create(CreateRunRequest("src","a"*64)).status,"CREATED")
 def test_hash(self):
  with self.assertRaises(APIError):RunAPI(S()).create(CreateRunRequest("s","x"))
 def test_get(self):
  a=RunAPI(S());a.create(CreateRunRequest("s","a"*64));self.assertEqual(a.get("r1").run_id,"r1")
 def test_missing(self):
  with self.assertRaises(APIError):RunAPI(S()).get("x")
 def test_list(self):
  a=RunAPI(S());a.create(CreateRunRequest("s","a"*64));self.assertEqual(len(a.list()),1)
if __name__=="__main__":unittest.main()
