
import unittest
from enterprise.environment_fingerprint import *
class T(unittest.TestCase):
 def test_fields(self):
  fp=build_environment_fingerprint(); self.assertIn("python_version",fp); self.assertIn("platform",fp)
 def test_extra(self): self.assertEqual(build_environment_fingerprint({"node":"22"})["node"],"22")
 def test_hash_deterministic(self): self.assertEqual(fingerprint_hash({"a":"1","b":"2"}),fingerprint_hash({"b":"2","a":"1"}))
 def test_hash_changes(self): self.assertNotEqual(fingerprint_hash({"a":"1"}),fingerprint_hash({"a":"2"}))
 def test_empty_rejected(self):
  with self.assertRaises(FingerprintError): fingerprint_hash({})
 def test_bad_extra_key(self):
  with self.assertRaises(FingerprintError): build_environment_fingerprint({1:"x"})
if __name__=="__main__": unittest.main()
