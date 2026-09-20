import unittest
from bie.scene_ir.scene_ir_semver import *
class TestSemver(unittest.TestCase):
 def test_parse(self):self.assertEqual(str(SceneIRVersion.parse("1.2.3")),"1.2.3")
 def test_bad(self):
  with self.assertRaises(SceneIRVersionError):SceneIRVersion.parse("1.2")
 def test_compat(self):self.assertEqual(compatibility("1.1.0","1.2.0"),"COMPATIBLE")
 def test_old_reader(self):self.assertEqual(compatibility("1.2.0","1.1.0"),"READER_TOO_OLD")
 def test_major(self):self.assertEqual(compatibility("2.0.0","1.9.0"),"INCOMPATIBLE")
 def test_minor_bump(self):self.assertEqual(required_bump("add_optional_field"),"MINOR")
 def test_major_bump(self):self.assertEqual(required_bump("remove_field"),"MAJOR")
 def test_next(self):self.assertEqual(next_version("1.2.3","MINOR"),"1.3.0")
