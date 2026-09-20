import unittest
from pathlib import Path
from bie.visual_intelligence.rep_original_codec import (
    EXPECTED_REP_ARCHIVE_SHA256, verify_rep_archive_directory, verify_rep_archive_bytes
)
ROOT=Path(__file__).resolve().parents[2]
REP_DIR=ROOT/"source_artifacts"/"rep_rebuilt"
class T(unittest.TestCase):
 def test_present(self): self.assertEqual(len(list(REP_DIR.glob("BIE_VIS_REP_*.zip"))),8)
 def test_directory_verifies(self):
  r=verify_rep_archive_directory(REP_DIR);self.assertTrue(r.all_verified);self.assertEqual(len(r.verified),8);self.assertEqual(r.missing,());self.assertEqual(r.mismatched,())
 def test_each_hash(self):
  for name in sorted(EXPECTED_REP_ARCHIVE_SHA256):
   self.assertTrue(verify_rep_archive_bytes(name,(REP_DIR/name).read_bytes()))
