
import unittest
from enterprise.backup_restore import *
class T(unittest.TestCase):
 def b(self,**k):
  d=dict(backup_id="b",db_ref="d",object_index_ref="o",created_at=1,schema_version=1,verified=True);d.update(k);return BackupManifest(**d)
 def test_valid(self):self.assertTrue(validate_backup(self.b()))
 def test_verify(self):
  with self.assertRaises(BackupError):validate_backup(self.b(verified=False))
 def test_plan(self):self.assertEqual(restore_plan(self.b(),"staging")[-1],"reconcile_catalog")
 def test_prod(self):
  with self.assertRaises(BackupError):restore_plan(self.b(),"production")
 def test_refs(self):
  with self.assertRaises(BackupError):validate_backup(self.b(db_ref=""))
if __name__=="__main__":unittest.main()
