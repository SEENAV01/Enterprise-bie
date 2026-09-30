import hashlib,json,stat,sys,zipfile
from pathlib import Path
from helpers import Base
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from verify_section17_package import PackageError,verify,extract

class PackageTests(Base):
    def manifest(self):
        p=self.root/'bundle';p.mkdir();(p/'x.txt').write_text('hello')
        (p/'MANIFEST.json').write_text(json.dumps({'schema_version':'1.0.0','files':{'x.txt':hashlib.sha256(b'hello').hexdigest()}}))
        return p
    def archive(self,names):
        path=self.root/'test.zip'
        with zipfile.ZipFile(path,'w') as z:
            for n in names:z.writestr(n,b'payload')
        return path
    def test_exact_manifest_verifies(self):self.assertEqual('VERIFIED',verify(self.manifest())['status'])
    def test_changed_byte_rejected(self):
        p=self.manifest();(p/'x.txt').write_text('tampered')
        with self.assertRaises(PackageError):verify(p)
    def test_missing_file_rejected(self):
        p=self.manifest();(p/'x.txt').unlink()
        with self.assertRaises(PackageError):verify(p)
    def test_unexpected_file_rejected(self):
        p=self.manifest();(p/'extra').write_text('unexpected')
        with self.assertRaises(PackageError):verify(p)
    def test_symlink_rejected(self):
        p=self.manifest();(p/'link').symlink_to(self.root)
        with self.assertRaises(PackageError):verify(p)
    def test_duplicate_manifest_key_rejected(self):
        p=self.manifest();(p/'MANIFEST.json').write_text('{"schema_version":"1.0.0","files":{},"files":{}}')
        with self.assertRaises(PackageError):verify(p)
    def test_valid_archive_extracted(self):
        p=self.archive(['root/a','root/b']);out=self.root/'extracted';extract(p,out);self.assertEqual(b'payload',(out/'root/a').read_bytes())
    def test_parent_path_escape_rejected_before_writing(self):
        p=self.archive(['good','../escape']);out=self.root/'extracted'
        with self.assertRaises(PackageError):extract(p,out)
        self.assertFalse(out.exists())
    def test_windows_path_escape_rejected(self):
        p=self.archive(['..\\escape'])
        with self.assertRaises(PackageError):extract(p,self.root/'out')
    def test_case_colliding_members_rejected(self):
        p=self.archive(['root/File','root/file'])
        with self.assertRaises(PackageError):extract(p,self.root/'out')
    def test_zip_symlink_rejected(self):
        path=self.root/'link.zip'
        with zipfile.ZipFile(path,'w') as z:
            i=zipfile.ZipInfo('link');i.create_system=3;i.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(i,'/etc/passwd')
        with self.assertRaises(PackageError):extract(path,self.root/'out')
    def test_file_directory_conflict_rejected(self):
        p=self.archive(['root/a','root/a/b'])
        with self.assertRaises(PackageError):extract(p,self.root/'out')
    def test_existing_destination_not_overwritten(self):
        p=self.archive(['a']);out=self.root/'out';out.mkdir();(out/'keep').write_text('keep')
        with self.assertRaises(PackageError):extract(p,out)
        self.assertEqual('keep',(out/'keep').read_text())
