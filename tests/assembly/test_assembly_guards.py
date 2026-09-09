import importlib.util
import io
from pathlib import Path
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from assembly_lib import inspect_zip, digest, normalize_imports, resolve_version, safe_path


def archive(entries):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:
        for name,data in entries:z.writestr(name,data)
    return stream.getvalue()


class AssemblyGuards(unittest.TestCase):
    def test_archive_sha_and_member_bytes(self):
        raw=archive([('source.py',b'original\n')]);self.assertEqual(inspect_zip(raw,digest(raw)),{'source.py':b'original\n'})
    def test_wrong_hash_refused(self):
        with self.assertRaises(ValueError):inspect_zip(archive([('x','a')]),'0'*64)
    def test_zip_slip_refused(self):
        for path in ('../x','/x','a/../../x','C:/x','a\\x','./x','a//x','.git/config'):
            with self.subTest(path=path),self.assertRaises(ValueError):inspect_zip(archive([(path,'x')]))
    def test_case_collision_refused(self):
        with self.assertRaises(ValueError):inspect_zip(archive([('a.py','x'),('A.py','y')]))
    def test_file_directory_collision_refused(self):
        with self.assertRaises(ValueError):inspect_zip(archive([('a','x'),('a/b','y')]))
    def test_symlink_refused(self):
        entry=zipfile.ZipInfo('link');entry.create_system=3;entry.external_attr=(0o120777<<16)
        with self.assertRaises(ValueError):inspect_zip(archive([(entry,'../outside')]))
    def test_expansion_limit(self):
        with self.assertRaises(ValueError):inspect_zip(archive([('x','12345')]),max_bytes=4)
    def test_conflict_requires_resolution(self):
        self.assertEqual(resolve_version([{'sha256':'a'},{'sha256':'b'}])['status'],'CONFLICT')
    def test_explicit_conflict_winner(self):
        self.assertEqual(resolve_version([{'sha256':'a'},{'sha256':'b'}],'b')['selected']['sha256'],'b')
    def test_identical_duplicates(self):
        self.assertEqual(resolve_version([{'sha256':'a'},{'sha256':'a'}])['status'],'RESOLVED')
    def test_import_only_rewrite(self):
        raw='from app.bie.enterprise.run_state import RunStateMachine\ns = "app.bie.enterprise.run_state"\n'
        normalized=normalize_imports(raw,{'enterprise'},{});self.assertIn('from bie.infrastructure.run_state',normalized);self.assertIn('s = "app.bie.enterprise.run_state"',normalized)
    def test_ambiguous_import_requires_review(self):
        raw='from equation_semantics import *\n';self.assertEqual(normalize_imports(raw,{'math_intelligence','knowledge_intelligence'},{}),raw)
