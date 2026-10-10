"""Pure source-guard/audit controls, not Linux browser or renderer evidence."""
import ast
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from bie.compiler.qa_common import CompilerQAError
from scripts import compiler_media_source_pin_amendment as audit
ROOT=Path(__file__).resolve().parents[2]
PAINTER=ROOT/'bie/compiler/real_paint.py'
OLD=ROOT/'docs/productization/task036-media-source-pin-amendment/real_paint.py.before'


def source_guard(source):
    fn=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='produce_actual_paint')
    pin=next(n for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='media_helper_sha256' for t in n.targets))
    guard=next(n for n in fn.body if isinstance(n,ast.If) and n.lineno==pin.lineno+1)
    return ast.Module(body=[pin,guard],type_ignores=[])


def execute_guard(source,actual,policy={}):
    # Exact production guard AST, with a declared scalar hash input. This does
    # not mock native compiler imports or claim Windows has Unix file hashing.
    ns={'media_thread_policy':policy,'media_helper':object(),
        'file_hash':lambda _: (actual,3632),'CompilerQAError':CompilerQAError}
    exec(compile(ast.fix_missing_locations(source_guard(source)),'source-guard-control','exec'),ns)
    return ns['media_helper_sha256']


class MediaSourcePin(unittest.TestCase):
    def test_before_actual_helper_rejected_by_exact_old_guard(self):
        with self.assertRaisesRegex(CompilerQAError,'^M1_MEDIA_THREAD_SOURCE_IDENTITY$'):
            execute_guard(OLD.read_text(),audit.HELPER_SHA256)

    def test_after_actual_helper_matches_explicit_pin(self):
        actual=sha256((ROOT/audit.HELPER).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
        self.assertEqual(execute_guard(PAINTER.read_text(),actual),audit.HELPER_SHA256)

    def test_changed_helper_still_rejected(self):
        with self.assertRaisesRegex(CompilerQAError,'^M1_MEDIA_THREAD_SOURCE_IDENTITY$'):
            execute_guard(PAINTER.read_text(),'a'*64)

    def test_legacy_no_policy_does_not_read_helper(self):
        for path in (OLD,PAINTER):
            tree=source_guard(path.read_text());calls=[]
            def forbidden(_):calls.append(1);raise AssertionError('LEGACY_HASHED')
            ns={'media_thread_policy':None,'media_helper':object(),'file_hash':forbidden,'CompilerQAError':CompilerQAError}
            exec(compile(ast.fix_missing_locations(tree),'source-guard-control','exec'),ns)
            self.assertEqual(calls,[])

    def test_painter_only_literal_pin_changed(self):
        old=OLD.read_text();new=PAINTER.read_text()
        self.assertEqual(old.replace("media_helper_sha256='1c6797c23509346cca5626c3c9e760624401cf4c2e46f79aa849f9eb5e540c8d'",
                                    "media_helper_sha256='"+audit.HELPER_SHA256+"'"),new)

    def test_pre_and_post_identity_checks_remain(self):
        text=PAINTER.read_text()
        self.assertEqual(text.count('file_hash(media_helper)[0]!=media_helper_sha256'),2)
        self.assertLess(text.index("raise CompilerQAError('M1_MEDIA_THREAD_SOURCE_IDENTITY')"),
                        text.index('process,kernel=run_chromium_isolated('))

    def test_new_native_error_codes_allowlisted_without_detail(self):
        from tests.compiler.run_motion_m1 import safe_error
        for code in ('M1_MEDIA_THREAD_SOURCE_IDENTITY','M1_MEDIA_THREAD_EXECUTION_IDENTITY'):
            self.assertEqual(safe_error(CompilerQAError(code+':FAKE_PRIVATE_TEXT')),
                {'exception_class':'CompilerQAError','safe_code':code})


class MediaSourcePinAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=audit.validate(ROOT)
        tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(tmp.cleanup);cls.root=Path(tmp.name)
        shutil.copytree(ROOT/'docs/productization',cls.root/'docs/productization',ignore=shutil.ignore_patterns('*.zip'))
        shutil.copytree(ROOT/'scripts',cls.root/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
        (cls.root/'manifests').mkdir()
        shutil.copyfile(ROOT/'manifests/post_dir_integration_004.json',cls.root/'manifests/post_dir_integration_004.json')
        for p in ('bie/compiler/real_paint.py','bie/compiler/qa_support/remotion_raster_capture.cjs',audit.HELPER):
            target=cls.root/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,target)

    def test_exact_git_preimages_and_complete_previous_chain(self):
        from scripts import compiler_media_policy_observation_amendment as previous
        self.assertEqual(audit.validate(self.root),self.doc);previous.validate(self.root)
        for row in self.doc['replacements']:
            original=subprocess.check_output(['git','show','f55f6915647816edc14cdb5ad043dedd2cdb39b2:'+row['path']],cwd=ROOT)
            self.assertEqual(original,(self.root/row['preimage']).read_bytes())

    def test_all_active_preimage_and_helper_tampers_rejected(self):
        paths=[audit.HELPER]+[r[k] for r in self.doc['replacements'] for k in ('path','preimage')]
        for relative in paths:
            path=self.root/relative;before=path.read_bytes()
            try:
                path.write_bytes(before+b'UNAUTHORIZED')
                with self.assertRaises(ValueError):audit.validate(self.root)
            finally:path.write_bytes(before)

    def test_prior_manifest_immutable(self):
        path=self.root/audit.PREVIOUS_DOCUMENT;before=path.read_bytes()
        try:
            path.write_bytes(before+b' ')
            with self.assertRaises(ValueError):audit.validate(self.root)
        finally:path.write_bytes(before)

    def test_recomputed_duplicate_extra_and_self_blessing_rejected(self):
        import json
        path=self.root/audit.DOCUMENT;before=path.read_bytes()
        try:
            for kind in ('duplicate','extra','bless'):
                value=deepcopy(self.doc)
                if kind=='bless':value['replacements'][0]['active_sha256']='f'*64
                else:
                    item=deepcopy(value['replacements'][0])
                    if kind=='extra':item['path']='bie/compiler/unapproved.py'
                    value['replacements'].append(item)
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):audit.validate(self.root)
        finally:path.write_bytes(before)

    def test_unlisted_previous_amendment_path_rejected(self):
        path=self.root/'bie/compiler/qa_support/remotion_raster_capture.cjs';before=path.read_bytes()
        try:
            path.write_bytes(before+b'UNAUTHORIZED')
            with self.assertRaises(ValueError):audit.validate(self.root)
        finally:path.write_bytes(before)

    def test_foreign_parent_or_target_rejected(self):
        for path in ('bie/compiler/unapproved.py','bie/compiler/real_paint.py'):
            with self.assertRaises(ValueError):audit.authenticated_previous_bytes(self.root,path,'a'*64)

    def test_inventory_once_without_native_safety_or_inherited_overlap(self):
        from tests.compiler import run_m1_tests as runner
        lanes,inherited=runner.inventory();path='tests/compiler/test_m1_media_source_pin.py'
        self.assertEqual(lanes['new'].count(path),1);self.assertEqual(len(lanes['native-extra']),214)
        self.assertNotIn(path,lanes['native-extra']);self.assertNotIn(path,lanes['safety']);self.assertNotIn(path,inherited)


if __name__=='__main__':unittest.main()
