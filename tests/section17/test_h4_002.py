import unittest,tempfile,shutil
from pathlib import Path
from bie.evaluation.benchmarks.browser.bundle import freeze
from bie.evaluation.benchmarks.browser.contracts import BrowserLimits
from h4_support import GAME,candidate,assert_error
class H4002(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'game';shutil.copytree(GAME,self.root)
 def tearDown(self):self.tmp.cleanup()
 def test_all_bytes_frozen(self):
  with freeze(self.root,candidate(self.root)) as (p,rec):
   self.assertEqual((p/'game.js').read_bytes(),(self.root/'game.js').read_bytes());self.assertEqual(len(rec['files']),3)
 def test_private_copy_survives_source_change(self):
  with freeze(self.root,candidate(self.root)) as (p,_):
   old=(p/'game.js').read_bytes();(self.root/'game.js').write_text('changed');self.assertEqual((p/'game.js').read_bytes(),old)
 def test_tampered_hash_blocks(self):
  c=candidate(self.root);(self.root/'game.js').write_text('tamper');assert_error(self,lambda:self._open(c))
 def _open(self,c):
  with freeze(self.root,c):pass
 def test_symlink_file_blocks(self):
  c=candidate(self.root);p=self.root/'game.js';p.unlink();p.symlink_to(GAME/'game.js');assert_error(self,lambda:self._open(c))
 def test_symlink_root_blocks(self):
  p=Path(self.tmp.name)/'link';p.symlink_to(self.root,target_is_directory=True)
  with self.assertRaises(Exception):
   with freeze(p,candidate(self.root)):pass
 def test_missing_file_blocks(self):
  c=candidate(self.root);(self.root/'styles.css').unlink();assert_error(self,lambda:self._open(c))
 def test_empty_file_blocks(self):
  (self.root/'game.js').write_text('');assert_error(self,lambda:self._open(candidate(self.root)))
 def test_temporary_assets_removed(self):
  with freeze(self.root,candidate(self.root)) as (p,_):saved=p
  self.assertFalse(saved.exists())
