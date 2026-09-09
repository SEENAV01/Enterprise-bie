
import unittest
from enterprise.credential_scope import *
class T(unittest.TestCase):
 def g(self):return CredentialGrant("worker",frozenset({"artifact:write"}),100)
 def test_allow(self):self.assertTrue(authorize(self.g(),"artifact:write",50))
 def test_deny(self):
  with self.assertRaises(CredentialError):authorize(self.g(),"secret:read",50)
 def test_expired(self):
  with self.assertRaises(CredentialError):authorize(self.g(),"artifact:write",100)
 def test_subject(self):
  with self.assertRaises(CredentialError):authorize(CredentialGrant("",frozenset({"x"}),10),"x",1)
if __name__=="__main__":unittest.main()
