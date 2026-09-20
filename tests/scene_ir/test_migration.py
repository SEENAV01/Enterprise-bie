import unittest
from bie.scene_ir.scene_ir_migration import *
class TestMigration(unittest.TestCase):
 def test_noop(self):
  d,r=migrate_scene_ir({"schema_version":"1.0.0"},"1.0.0");self.assertEqual(r.rules_applied,())
 def test_forward(self):
  d,r=migrate_scene_ir({"schema_version":"1.0.0"},"1.1.0");self.assertEqual(d["schema_version"],"1.1.0")
 def test_history(self):
  d,r=migrate_scene_ir({"schema_version":"1.0.0"},"1.1.0");self.assertIn("migration_history",d["metadata"])
 def test_to12(self):
  d,r=migrate_scene_ir({"schema_version":"1.0.0"},"1.2.0");self.assertIn("compiler_capabilities",d)
 def test_major(self):
  with self.assertRaises(SceneIRMigrationError):migrate_scene_ir({"schema_version":"1.0.0"},"2.0.0")
 def test_down(self):
  with self.assertRaises(SceneIRMigrationError):migrate_scene_ir({"schema_version":"1.2.0"},"1.1.0")
 def test_receipt(self):
  _,r=migrate_scene_ir({"schema_version":"1.0.0"},"1.1.0");self.assertTrue(validate_migration_receipt(r))
 def test_not_accepted(self):
  _,r=migrate_scene_ir({"schema_version":"1.0.0"},"1.1.0");self.assertFalse(r.accepted)
