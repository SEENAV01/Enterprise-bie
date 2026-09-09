
import unittest
from bie.document_intelligence.source_hash import *
class T(unittest.TestCase):
 def test_len(self):self.assertEqual(len(source_sha256(b"x")),64)
 def test_stable(self):self.assertEqual(source_sha256(b"x"),source_sha256(b"x"))
 def test_diff(self):self.assertNotEqual(source_sha256(b"x"),source_sha256(b"y"))
 def test_same(self):self.assertTrue(same_source(b"abc",b"abc"))
 def test_empty(self):
  with self.assertRaises(HashError):source_sha256(b"")
if __name__=="__main__":unittest.main()
