
import unittest
from bie.infrastructure.audit_log import *
class T(unittest.TestCase):
 def test_append(self):self.assertEqual(AuditLog().append("u","read","r",1).seq,1)
 def test_chain(self):
  a=AuditLog();x=a.append("u","a","r",1);y=a.append("u","b","r",2);self.assertEqual(y.prev_hash,x.entry_hash)
 def test_verify(self):
  a=AuditLog();a.append("u","a","r",1);a.append("u","b","r",2);self.assertTrue(a.verify())
 def test_required(self):
  with self.assertRaises(AuditError):AuditLog().append("","a","r",1)
 def test_genesis(self):self.assertEqual(AuditLog().append("u","a","r",1).prev_hash,"GENESIS")
if __name__=="__main__":unittest.main()
