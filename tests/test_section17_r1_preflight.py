"""Read-only integration preflight tests. Not a Section17/full-repository gate."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('section17_preflight', ROOT/'scripts/section17_r1_preflight.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)

class PathChecks(unittest.TestCase):
    def test_plain_path(self): self.assertEqual(str(p.safe('bie/evaluation/benchmarks/a.py')), 'bie/evaluation/benchmarks/a.py')
    def test_traversal_and_absolute(self):
        for value in ('../a', '/a', 'a/../b', 'a//b', './a', '', 'C:/a', 'a\\b'):
            with self.subTest(value=value), self.assertRaises(p.PreflightError): p.safe(value)
    def test_windows_aliases(self):
        for value in ('NUL.txt', 'a/COM1.py', 'a./b', 'a /b'):
            with self.subTest(value=value), self.assertRaises(p.PreflightError): p.safe(value)
    def test_controls_and_unicode_alias(self):
        for value in ('a\nb', 'a\0b', 'e\u0301.txt'):
            with self.subTest(value=value), self.assertRaises(p.PreflightError): p.safe(value)
    def test_duplicate_json(self):
        with self.assertRaisesRegex(p.PreflightError, 'DUPLICATE'): p.load(b'{"a":1,"a":2}')
    def test_valid_json(self): self.assertEqual(p.load(b'{"a":1}'), {'a':1})
    def test_file_hash(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'a';f.write_bytes(b'abc');self.assertEqual(p.file_hash(f),p.sha(b'abc'))
    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(p.PreflightError): p.file_hash(Path(d)/'absent')
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'a';f.write_bytes(b'abc');g=Path(d)/'link';g.symlink_to(f)
            with self.assertRaisesRegex(p.PreflightError,'SYMLINK'):p.file_hash(g)

class Dispositions(unittest.TestCase):
    def row(self, role=p.SOURCE,path='bie/evaluation/benchmarks/a.py',value=None):
        return {'path':path,'disposition':role,'sha256':value or 'a'*64,'bytes':3}
    def test_source_add(self):self.assertEqual(p.classify(self.row(),None),'ADD_REVIEW_CANDIDATE')
    def test_identical(self):self.assertEqual(p.classify(self.row(),'a'*64),'IDENTICAL')
    def test_collision(self):self.assertEqual(p.classify(self.row(),'b'*64),'CONFLICT_EXISTING_FILE')
    def test_source_scope(self):
        with self.assertRaisesRegex(p.PreflightError,'SOURCE_SCOPE'):p.classify(self.row(path='bie/other.py'),None)
    def test_test_scope(self):
        with self.assertRaisesRegex(p.PreflightError,'TEST_SCOPE'):p.classify(self.row(p.TESTS,'tests/other.py'),None)
    def test_dependency_never_overlay(self):
        row=self.row(p.DEPENDENCY,'bie/qa/example.py')
        for old in (None,'b'*64):self.assertEqual(p.classify(row,old),'DEPENDENCY_REVIEW_DO_NOT_COPY')
        self.assertEqual(p.classify(row,'a'*64),'DEPENDENCY_IDENTICAL_DO_NOT_COPY')
    def test_legacy_metadata_not_global(self):self.assertEqual(p.classify(self.row(p.HISTORY,'BIE_SECTION17_CONTINUATION.json'),None),'ARCHIVE_ONLY_NOT_GLOBAL_OVERLAY')
    def test_pycache_not_production(self):self.assertEqual(p.classify(self.row(path='bie/evaluation/benchmarks/__pycache__/a.pyc'),None),'ARCHIVE_ONLY_GENERATED_CACHE')
    def test_combined_cli_base(self):self.assertEqual(p.classify(self.row(p.PATCH,p.CLI,p.CLI_NEXT),p.CLI_BASE),'CLI_BASE_MATCH_REVIEW_PATCH')
    def test_combined_cli_candidate(self):self.assertEqual(p.classify(self.row(p.PATCH,p.CLI,p.CLI_NEXT),p.CLI_NEXT),'CLI_ALREADY_CANDIDATE')
    def test_changed_cli_blocks(self):self.assertEqual(p.classify(self.row(p.PATCH,p.CLI,p.CLI_NEXT),'f'*64),'CONFLICT_CLI')
    def test_other_patch_rejected(self):
        with self.assertRaisesRegex(p.PreflightError,'UNEXPECTED_PATCH'):p.classify(self.row(p.PATCH,'other.py'),None)
    def test_unknown_role_rejected(self):
        with self.assertRaisesRegex(p.PreflightError,'UNKNOWN_DISPOSITION'):p.classify(self.row('UNKNOWN'),None)
    def test_collision_plan_readonly(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=root/'bie/evaluation/benchmarks/a.py';path.parent.mkdir(parents=True);path.write_bytes(b'old')
            before={str(x.relative_to(root)):x.read_bytes() for x in root.rglob('*') if x.is_file()}
            rows=p.collision_plan(root,[self.row()]);self.assertEqual(rows[0]['disposition'],'CONFLICT_EXISTING_FILE')
            self.assertEqual(before,{str(x.relative_to(root)):x.read_bytes() for x in root.rglob('*') if x.is_file()})
    def test_directory_conflict(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'bie/evaluation/benchmarks/a.py').mkdir(parents=True)
            with self.assertRaisesRegex(p.PreflightError,'TARGET_NOT_FILE'):p.collision_plan(root,[self.row()])
    def test_wrong_master_size(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'a.zip';f.write_bytes(b'not a master')
            with self.assertRaisesRegex(p.PreflightError,'MASTER_SIZE'):p.verify_master(f)
    def test_wrong_master_hash(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'a.zip';f.write_bytes(b'not a master')
            with patch.object(p,'MASTER_BYTES',f.stat().st_size), self.assertRaisesRegex(p.PreflightError,'MASTER_HASH'):p.verify_master(f)

class CheckoutGuards(unittest.TestCase):
    def result(self, root, override=None):
        values={('rev-parse','--show-toplevel'):str(root),('remote','get-url','origin'):next(iter(p.ORIGINS)),('symbolic-ref','--short','HEAD'):p.BRANCH,('status','--porcelain','--untracked-files=all'):'',('rev-parse','origin/main'):p.BASE,('merge-base','--is-ancestor',p.BASE,'HEAD'):'',('rev-parse','HEAD'):'1'*40}
        if override:values.update(override)
        return lambda repo,*args:values[args]
    def test_clean_integration_context(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d)
            with patch.object(p,'git',side_effect=self.result(r)):self.assertEqual(p.check_checkout(r)['base'],p.BASE)
    def test_main_branch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d)
            with patch.object(p,'git',side_effect=self.result(r,{('symbolic-ref','--short','HEAD'):'main'})), self.assertRaisesRegex(p.PreflightError,'WRONG_BRANCH'):p.check_checkout(r)
    def test_dirty_checkout_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d)
            with patch.object(p,'git',side_effect=self.result(r,{('status','--porcelain','--untracked-files=all'):' M original.py'})), self.assertRaisesRegex(p.PreflightError,'DIRTY'):p.check_checkout(r)
    def test_changed_tracking_main_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d)
            with patch.object(p,'git',side_effect=self.result(r,{('rev-parse','origin/main'):'f'*40})), self.assertRaisesRegex(p.PreflightError,'MAIN_CHANGED'):p.check_checkout(r)
    def test_wrong_origin_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d)
            with patch.object(p,'git',side_effect=self.result(r,{('remote','get-url','origin'):'https://github.com/other/repo.git'})), self.assertRaisesRegex(p.PreflightError,'WRONG_ORIGIN'):p.check_checkout(r)

if __name__=='__main__':unittest.main(verbosity=2)
