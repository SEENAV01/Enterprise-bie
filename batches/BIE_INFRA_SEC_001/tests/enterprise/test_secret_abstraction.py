
import unittest
from enterprise.secret_abstraction import *
class T(unittest.TestCase):
 def test_resolve(self): self.assertEqual(SecretResolver({"env":lambda n,v:"x"}).resolve(SecretRef("env","API")),"x")
 def test_provider(self):
  with self.assertRaises(SecretError): SecretResolver({}).resolve(SecretRef("x","A"))
 def test_name(self):
  with self.assertRaises(SecretError): SecretResolver({"e":lambda n,v:"x"}).resolve(SecretRef("e",""))
 def test_missing(self):
  with self.assertRaises(SecretError): SecretResolver({"e":lambda n,v:None}).resolve(SecretRef("e","A"))
 def test_no_literal_key(self):
  with self.assertRaises(SecretError): SecretResolver({"e":lambda n,v:"x"}).resolve(SecretRef("e","sk-secret"))
if __name__=="__main__":unittest.main()
