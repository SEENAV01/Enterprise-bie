
import unittest
from bie.infrastructure.benchmark_api import *
class R:
 def cases(self):return [{"id":"c","domain":"physics"}]
 def get(self,k):return {"id":"c"} if k=="c" else None
class X:
 def run(self,c,a):return {"case":c,"passed":True,"artifacts":a}
class T(unittest.TestCase):
 def test_cases(self):self.assertEqual(len(BenchmarkAPI(R(),X()).cases()),1)
 def test_filter(self):self.assertEqual(len(BenchmarkAPI(R(),X()).cases("math")),0)
 def test_run(self):self.assertTrue(BenchmarkAPI(R(),X()).run("c",["a"])["passed"])
 def test_missing(self):
  with self.assertRaises(BenchmarkAPIError):BenchmarkAPI(R(),X()).run("x",["a"])
 def test_artifacts(self):
  with self.assertRaises(BenchmarkAPIError):BenchmarkAPI(R(),X()).run("c",[])
if __name__=="__main__":unittest.main()
