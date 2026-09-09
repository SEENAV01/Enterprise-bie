
import unittest
from model_gateway.rate_limit import *
class T(unittest.TestCase):
 def test_consume(self):b=Bucket(10,5,1,0);self.assertTrue(consume(b,3,0))
 def test_deny(self):b=Bucket(10,1,0,0);self.assertFalse(consume(b,2,0))
 def test_refill(self):b=Bucket(10,0,1,0);self.assertTrue(consume(b,2,2))
 def test_cap(self):b=Bucket(10,9,10,0);consume(b,1,10);self.assertEqual(b.tokens,9)
 def test_bad(self):
  with self.assertRaises(RateLimitError):consume(Bucket(0,0,1,0),1,1)
if __name__=="__main__":unittest.main()
