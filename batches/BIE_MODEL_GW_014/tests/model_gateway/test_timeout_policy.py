
import unittest
from model_gateway.timeout_policy import *
class T(unittest.TestCase):
 def test_ok(self):self.assertTrue(validate(TimeoutPolicy(2,30,35)))
 def test_zero(self):
  with self.assertRaises(TimeoutPolicyError):validate(TimeoutPolicy(0,1,1))
 def test_total(self):
  with self.assertRaises(TimeoutPolicyError):validate(TimeoutPolicy(1,10,5))
 def test_remaining(self):self.assertEqual(remaining(10,7),3)
 def test_expired(self):self.assertEqual(remaining(5,7),0)
if __name__=="__main__":unittest.main()
