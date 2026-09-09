
import unittest
from bie.infrastructure.queue_health import *
class T(unittest.TestCase):
 def test_healthy(self): self.assertEqual(classify(QueueSnapshot(1,1,0,2)),"HEALTHY")
 def test_dlq(self): self.assertEqual(classify(QueueSnapshot(0,0,1,0)),"DEGRADED")
 def test_age(self): self.assertEqual(classify(QueueSnapshot(1,0,0,301)),"BACKLOGGED")
 def test_count(self): self.assertEqual(classify(QueueSnapshot(1001,0,0,1)),"BACKLOGGED")
 def test_invalid(self):
  with self.assertRaises(QueueHealthError): classify(QueueSnapshot(-1,0,0,0))
if __name__=="__main__": unittest.main()
