import unittest,tempfile,hashlib,zipfile,stat
from pathlib import Path
from bie.evaluation.benchmarks.browser.integrity import verify_inventory,inspect_zip
from h4_support import assert_error
class H4010(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
 def tearDown(self):self.t.cleanup()
 def test_recovered_hashes(self):
  (self.root/'a').write_bytes(b'a');self.assertTrue(verify_inventory(self.root,{'a':hashlib.sha256(b'a').hexdigest()})['all_matched'])
 def test_recovery_not_original_master_claim(self):
  (self.root/'a').write_bytes(b'a');self.assertFalse(verify_inventory(self.root,{'a':hashlib.sha256(b'a').hexdigest()})['original_master_bytes_recovered'])
 def test_missing_file_not_assumed(self):self.assertEqual(verify_inventory(self.root,{'a':'0'*64})['missing'],['a'])
 def test_changed_file_detected(self):
  (self.root/'a').write_bytes(b'a');self.assertEqual(verify_inventory(self.root,{'a':'0'*64})['changed'],['a'])
 def test_inventory_traversal_blocks(self):assert_error(self,lambda:verify_inventory(self.root,{'../a':'0'*64}),'RECOVERY_PATH_INVALID')
 def archive(self,name='safe.txt'):
  p=self.root/'out.zip'
  with zipfile.ZipFile(p,'w') as z:z.writestr(name,b'example')
  return p,hashlib.sha256(p.read_bytes()).hexdigest()
 def test_zip_crc_and_outer_hash(self):
  p,h=self.archive();self.assertTrue(inspect_zip(p,expected_sha256=h)['verified'])
 def test_wrong_archive_hash_blocks(self):
  p,_=self.archive();assert_error(self,lambda:inspect_zip(p,expected_sha256='0'*64),'ZIP_OUTER_HASH_MISMATCH')
 def test_zip_traversal_blocks(self):
  p,h=self.archive('../escape');assert_error(self,lambda:inspect_zip(p,expected_sha256=h),'ZIP_UNSAFE_MEMBER')
 def test_zip_member_limit_blocks(self):
  p,h=self.archive();assert_error(self,lambda:inspect_zip(p,expected_sha256=h,max_members=0),'ZIP_MEMBER_LIMIT')
 def test_zip_expansion_limit_blocks(self):
  p,h=self.archive();assert_error(self,lambda:inspect_zip(p,expected_sha256=h,max_bytes=1),'ZIP_BYTE_LIMIT')
