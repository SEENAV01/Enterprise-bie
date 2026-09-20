import unittest,tempfile,json,os,sys,shutil
from pathlib import Path
from bie.compiler.installed_toolchain import tree_inventory,collect_installed_toolchain,require_same_toolchain
from tests.compiler.h7_test_support import fake_node_tree

class InstalledIdentityTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.p=fake_node_tree(self.root/'p')
    def tearDown(self):self.tmp.cleanup()
    def collect(self):return collect_installed_toolchain(self.p,node=sys.executable,browser=sys.executable)
    def test_complete_inventory(self):self.assertEqual(self.collect()['node_tree']['file_count'],14)
    def test_file_mutation_changes_identity(self):
        a=self.collect();(self.p/'node_modules/react/index.js').write_text('changed');b=self.collect()
        with self.assertRaisesRegex(ValueError,'TOOLCHAIN_CHANGED'):require_same_toolchain(a,b)
    def test_order_independent_inventory(self):self.assertEqual(self.collect(),self.collect())
    def test_internal_bin_link_hashes_target(self):
        p=self.p/'node_modules/.bin';p.mkdir();(p/'react').symlink_to('../react/index.js');self.assertEqual(self.collect()['node_tree']['file_count'],15)
    def test_external_link_reject(self):
        (self.p/'node_modules/x').symlink_to('/etc/passwd')
        with self.assertRaisesRegex(ValueError,'EXTERNAL'):self.collect()
    def test_broken_link_reject(self):
        (self.p/'node_modules/x').symlink_to('absent')
        with self.assertRaisesRegex(ValueError,'BROKEN'):self.collect()
    def test_directory_link_reject(self):
        (self.p/'node_modules/x').symlink_to('react',target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'DIRECTORY_LINK'):self.collect()
    def test_required_package_missing(self):
        shutil.rmtree(self.p/'node_modules/react')
        with self.assertRaisesRegex(ValueError,'MISSING'):self.collect()
    def test_version_mismatch(self):
        p=self.p/'node_modules/react/package.json';p.write_text('{"version":"18.0.0"}')
        with self.assertRaisesRegex(ValueError,'VERSION_MISMATCH'):self.collect()
    def test_unlocked_package_reject(self):
        p=self.p/'node_modules/rogue';p.mkdir();(p/'package.json').write_text('{"version":"1.0.0"}')
        with self.assertRaisesRegex(ValueError,'UNLOCKED'):self.collect()
    def test_budget_no_sampling(self):
        with self.assertRaisesRegex(ValueError,'BUDGET'):tree_inventory(self.p/'node_modules',max_files=1)
    def test_fifo_reject_without_blocking(self):
        os.mkfifo(self.p/'node_modules/pipe')
        with self.assertRaisesRegex(ValueError,'FILE_TYPE'):self.collect()
    def test_receipt_tampering(self):
        a=self.collect();b=self.collect();b['tools']['node']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'TAMPERED'):require_same_toolchain(a,b)
    def test_no_signature_or_render_claim(self):self.assertEqual(self.collect()['authenticity'],'BYTE_IDENTITY_NOT_PUBLISHER_SIGNATURE');self.assertFalse(self.collect()['accepted'])
    def test_relocated_identical_tree(self):
        q=self.root/'q';shutil.copytree(self.p,q);a=self.collect();b=collect_installed_toolchain(q,node=sys.executable,browser=sys.executable);self.assertTrue(require_same_toolchain(a,b))
