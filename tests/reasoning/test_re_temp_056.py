import unittest
from bie.reasoning.temporal_migration_manifest import *

class T(unittest.TestCase):
    def e(self,task,target,hexchar="a"):
        return MigrationEntry(task,"src/"+target,target,hexchar*64)
    def test_deterministic(self):
        a=build_manifest([self.e("2","b.py"),self.e("1","a.py")])
        b=build_manifest([self.e("1","a.py"),self.e("2","b.py")])
        self.assertEqual(a,b)
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            build_manifest([self.e("1","a.py"),self.e("1","a.py","b")])
    def test_bad_hash_rejected(self):
        with self.assertRaises(ValueError):
            build_manifest([MigrationEntry("1","s","t","xyz")])
    def test_has_hash(self):
        self.assertEqual(len(build_manifest([self.e("1","a.py")])["manifest_sha256"]),64)
