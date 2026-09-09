
import unittest
from enterprise.network_policy import *
class T(unittest.TestCase):
 def test_allow(self):self.assertTrue(NetworkPolicy(["api.example.com"]).authorize("https://api.example.com/x"))
 def test_http(self):
  with self.assertRaises(NetworkSecurityError):NetworkPolicy(["a.com"]).authorize("http://a.com")
 def test_host(self):
  with self.assertRaises(NetworkSecurityError):NetworkPolicy(["a.com"]).authorize("https://b.com")
 def test_loopback(self):
  with self.assertRaises(NetworkSecurityError):NetworkPolicy(["127.0.0.1"]).authorize("https://127.0.0.1")
 def test_private(self):
  with self.assertRaises(NetworkSecurityError):NetworkPolicy(["10.0.0.1"]).authorize("https://10.0.0.1")
if __name__=="__main__":unittest.main()
