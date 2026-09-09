
import unittest
from enterprise.task_versioning import *
class T(unittest.TestCase):
 def test_create_v1(self): self.assertEqual(VersionLedger().create("x",{"a":1}).version,1)
 def test_duplicate_create(self):
  l=VersionLedger(); l.create("x",{})
  with self.assertRaises(VersionError): l.create("x",{})
 def test_revise_v2(self):
  l=VersionLedger(); l.create("x",{"a":1}); self.assertEqual(l.revise("x",{"a":2},"change").version,2)
 def test_supersedes(self):
  l=VersionLedger(); l.create("x",{"a":1}); self.assertEqual(l.revise("x",{"a":2},"change").supersedes,1)
 def test_same_spec_rejected(self):
  l=VersionLedger(); l.create("x",{"a":1})
  with self.assertRaises(VersionError): l.revise("x",{"a":1},"x")
 def test_reason_required(self):
  l=VersionLedger(); l.create("x",{"a":1})
  with self.assertRaises(VersionError): l.revise("x",{"a":2},"")
 def test_hash_deterministic(self): self.assertEqual(spec_hash({"a":1,"b":2}),spec_hash({"b":2,"a":1}))
 def test_history_immutable_tuple(self):
  l=VersionLedger(); l.create("x",{}); self.assertIsInstance(l.history("x"),tuple)
if __name__=="__main__": unittest.main()
