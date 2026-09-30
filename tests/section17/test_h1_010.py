import unittest
from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError, digest, canonical_json, strict_loads

import zipfile,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import verify_section17_package as package
class PortablePackageBoundary(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def archive(self,names):
        p=self.root/'archive.zip'
        with zipfile.ZipFile(p,'w') as z:
            for n in names:z.writestr(n,b'data')
        return p
    def valid_root(self):
        p=self.root/'good';p.mkdir();(p/'hello.txt').write_text('hello')
        (p/'MANIFEST.json').write_text(json.dumps({'schema_version':'1.0.0','files':{'hello.txt':hashlib.sha256(b'hello').hexdigest()}}));return p
    def test_verify_valid_tree(self):self.assertEqual('VERIFIED',package.verify(self.valid_root())['status'])
    def test_verify_symlink_root_refused(self):
        p=self.valid_root();link=self.root/'link';link.symlink_to(p,target_is_directory=True)
        with self.assertRaisesRegex(package.PackageError,'SYMLINK'):package.verify(link)
    def test_extract_symlink_parent_refused(self):
        target=self.root/'target';target.mkdir();link=self.root/'link';link.symlink_to(target,target_is_directory=True)
        with self.assertRaisesRegex(package.PackageError,'SYMLINK'):package.extract(self.archive(['safe.txt']),link/'output')
        self.assertFalse((target/'output').exists())
    def test_source_archive_symlink_refused(self):
        z=self.archive(['safe']);link=self.root/'link.zip';link.symlink_to(z)
        with self.assertRaisesRegex(package.PackageError,'SYMLINK'):package.extract(link,self.root/'out')
    def test_reserved_windows_device_refused(self):
        with self.assertRaises(package.PackageError):package.relative_name('a/NUL.txt')
    def test_trailing_dot_refused(self):
        with self.assertRaises(package.PackageError):package.relative_name('a./b')
    def test_trailing_space_refused(self):
        with self.assertRaises(package.PackageError):package.relative_name('a /b')
    def test_control_character_refused(self):
        with self.assertRaises(package.PackageError):package.relative_name('a\nb')
    def test_unicode_normalization_alias_zip_refused(self):
        z=self.archive(['é.txt','e\u0301.txt'])
        with self.assertRaisesRegex(package.PackageError,'DUPLICATE_ZIP_MEMBER'):package.extract(z,self.root/'out')
    def test_parent_traversal_zip_refused(self):
        with self.assertRaises(package.PackageError):package.extract(self.archive(['../evil']),self.root/'out')
    def test_file_directory_conflict_refused(self):
        with self.assertRaisesRegex(package.PackageError,'CONFLICT'):package.extract(self.archive(['a','a/b']),self.root/'out')
    def test_valid_unicode_member_works(self):
        package.extract(self.archive(['पाठ.txt']),self.root/'out');self.assertEqual(b'data',(self.root/'out'/'पाठ.txt').read_bytes())
    def test_extra_unmanifested_file_rejected(self):
        root=self.valid_root();(root/'extra').write_text('extra')
        with self.assertRaisesRegex(package.PackageError,'INVENTORY_MISMATCH'):package.verify(root)
    def test_tampered_bytes_rejected(self):
        root=self.valid_root();(root/'hello.txt').write_text('changed')
        with self.assertRaisesRegex(package.PackageError,'HASH_MISMATCH'):package.verify(root)
