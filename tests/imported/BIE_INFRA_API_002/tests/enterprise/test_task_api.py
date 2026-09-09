
import unittest
from bie.infrastructure.task_api import *
class R:
 def __init__(self):self.x={"a":{"task_id":"a","status":"READY"}}
 def get(self,k):return self.x.get(k)
 def all(self):return self.x.values()
 def transition(self,k,t,r,e):self.x[k]["status"]=t;return self.x[k]
class T(unittest.TestCase):
 def test_get(self):self.assertEqual(TaskAPI(R()).get("a")["status"],"READY")
 def test_missing(self):
  with self.assertRaises(TaskAPIError):TaskAPI(R()).get("x")
 def test_list(self):self.assertEqual(len(TaskAPI(R()).list("READY")),1)
 def test_filter(self):self.assertEqual(len(TaskAPI(R()).list("ACCEPTED")),0)
 def test_transition(self):self.assertEqual(TaskAPI(R()).transition("a","IN_PROGRESS","start")["status"],"IN_PROGRESS")
 def test_reason(self):
  with self.assertRaises(TaskAPIError):TaskAPI(R()).transition("a","X","")
if __name__=="__main__":unittest.main()
