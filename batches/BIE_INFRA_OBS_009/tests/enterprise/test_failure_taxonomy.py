
import unittest
from enterprise.failure_taxonomy import *
class T(unittest.TestCase):
 def test_valid(self): self.assertEqual(make_failure("RENDER","R1","ERROR",True,"compiler","x").category,"RENDER")
 def test_category(self):
  with self.assertRaises(FailureError): make_failure("X","1","ERROR",False,"o","m")
 def test_severity(self):
  with self.assertRaises(FailureError): make_failure("INFRA","1","BAD",False,"o","m")
 def test_required(self):
  with self.assertRaises(FailureError): make_failure("INFRA","","ERROR",False,"o","m")
 def test_retryable(self): self.assertTrue(make_failure("INFRA","Q","ERROR",True,"infra","queue").retryable)
if __name__=="__main__": unittest.main()
