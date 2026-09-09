
import unittest
from bie.model_gateway.retry_policy import *
class T(unittest.TestCase):
 def p(self):return RetryPolicy(3,1,4)
 def test_retry(self):self.assertTrue(should_retry("timeout",1,self.p()))
 def test_no_retry(self):self.assertFalse(should_retry("schema_error",1,self.p()))
 def test_exhaust(self):self.assertFalse(should_retry("timeout",3,self.p()))
 def test_backoff(self):self.assertEqual(delay(3,self.p()),4)
 def test_bad(self):
  with self.assertRaises(RetryError):validate(RetryPolicy(0,1,2))
if __name__=="__main__":unittest.main()
