
import unittest
from enterprise.worker_health import *
class T(unittest.TestCase):
 def h(self,**k):
  d=dict(worker_id="w",timestamp=100,active_tasks=1,capacity=2,error_rate=0);d.update(k);return WorkerHeartbeat(**d)
 def test_healthy(self): self.assertEqual(classify(self.h(),110),"HEALTHY")
 def test_stale(self): self.assertEqual(classify(self.h(),200),"STALE")
 def test_over(self): self.assertEqual(classify(self.h(active_tasks=3),110),"OVERLOADED")
 def test_degraded(self): self.assertEqual(classify(self.h(error_rate=.5),110),"DEGRADED")
 def test_invalid(self):
  with self.assertRaises(WorkerHealthError): classify(self.h(capacity=0),110)
if __name__=="__main__": unittest.main()
