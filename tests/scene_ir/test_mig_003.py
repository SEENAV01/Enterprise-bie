import unittest
from bie.scene_ir.legacy_retirement import *
class T(unittest.TestCase):
 def p(self):return LegacyRetirementPolicy("legacy",True,False,True,"2.0.0","replace")
 def test_write_block(self):self.assertEqual(evaluate_legacy_use(self.p(),operation="write").action,"BLOCK")
 def test_import_needs_evidence(self):self.assertEqual(evaluate_legacy_use(self.p(),operation="import").action,"BLOCK")
 def test_import_migrate(self):self.assertEqual(evaluate_legacy_use(self.p(),operation="import",has_migration_evidence=True).action,"MIGRATE")
 def test_policy(self):self.assertEqual(len(default_retirement_policies()),2)
 def test_operation(self):
  with self.assertRaises(DSLMigrationError):evaluate_legacy_use(self.p(),operation="delete")
 def test_version_warning(self):self.assertTrue(evaluate_legacy_use(self.p(),operation="write",current_version="2.0.0").warnings)
 def test_not_accepted(self):self.assertFalse(evaluate_legacy_use(self.p(),operation="write").accepted)
