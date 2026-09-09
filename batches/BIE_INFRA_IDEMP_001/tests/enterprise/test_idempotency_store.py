
import unittest,tempfile,os
from enterprise.idempotency_store import *
class T(unittest.TestCase):
 def setUp(self): self.f=tempfile.NamedTemporaryFile(delete=False); self.f.close(); self.s=SQLiteIdempotencyStore(self.f.name)
 def tearDown(self): self.s.close(); os.unlink(self.f.name)
 def test_claim(self): self.assertEqual(self.s.claim("k","f","w").state,"CLAIMED")
 def test_same_claim(self): self.s.claim("k","f","w"); self.assertEqual(self.s.claim("k","f","w").fingerprint,"f")
 def test_conflict(self):
  self.s.claim("k","f","w")
  with self.assertRaises(IdempotencyError): self.s.claim("k","x","w")
 def test_complete(self): self.s.claim("k","f","w"); self.assertEqual(self.s.complete("k","w","a").state,"COMPLETED")
 def test_foreign(self):
  self.s.claim("k","f","w")
  with self.assertRaises(IdempotencyError): self.s.complete("k","x","a")
 def test_result_conflict(self):
  self.s.claim("k","f","w"); self.s.complete("k","w","a")
  with self.assertRaises(IdempotencyError): self.s.complete("k","w","b")
 def test_restart(self):
  self.s.claim("k","f","w"); self.s.close(); self.s=SQLiteIdempotencyStore(self.f.name); self.assertEqual(self.s.get("k").state,"CLAIMED")
 def test_required(self):
  with self.assertRaises(IdempotencyError): self.s.claim("","","")
if __name__=="__main__": unittest.main()
