
import unittest
from bie.infrastructure.metrics import *
class T(unittest.TestCase):
 def test_counter(self): m=Metrics();m.inc("x");m.inc("x",2);self.assertEqual(m.counters["x"],3)
 def test_negative_counter(self):
  with self.assertRaises(MetricError): Metrics().inc("x",-1)
 def test_gauge(self): m=Metrics();m.gauge("q",4);self.assertEqual(m.gauges["q"],4)
 def test_hist(self): m=Metrics();m.observe("lat",1.2);self.assertEqual(m.histograms["lat"],[1.2])
 def test_snapshot_tuple(self): m=Metrics();m.observe("x",1);self.assertEqual(m.snapshot()["histograms"]["x"],(1,))
if __name__=="__main__": unittest.main()
