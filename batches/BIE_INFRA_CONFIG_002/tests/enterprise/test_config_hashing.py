
import unittest
from enterprise.config_hashing import *
class T(unittest.TestCase):
 def test_deterministic(self): self.assertEqual(config_hash({"a":1,"b":2}),config_hash({"b":2,"a":1}))
 def test_changes(self): self.assertNotEqual(config_hash({"a":1}),config_hash({"a":2}))
 def test_length(self): self.assertEqual(len(config_hash({})),64)
 def test_verify(self):
  h=config_hash({"x":1}); self.assertTrue(verify_hash({"x":1},h))
 def test_verify_false(self):
  h=config_hash({"x":1}); self.assertFalse(verify_hash({"x":2},h))
 def test_bad_expected(self):
  with self.assertRaises(ConfigHashError): verify_hash({},"x")
 def test_non_dict(self):
  with self.assertRaises(ConfigHashError): config_hash([])
if __name__=="__main__": unittest.main()
