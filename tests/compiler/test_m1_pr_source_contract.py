"""Pure exact-source/audit compatibility, not browser or rendered evidence."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from scripts import compiler_pr_source_contract_amendment as audit
ROOT=Path(__file__).resolve().parents[2]
from tests.source_baseline_fixture import overlay_baseline

class PRSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=audit.validate(ROOT)
        temp=tempfile.TemporaryDirectory();cls.addClassCleanup(temp.cleanup);cls.root=Path(temp.name)
        for folder in ('bie/compiler','docs/productization','scripts'):
            shutil.copytree(ROOT/folder,cls.root/folder,ignore=shutil.ignore_patterns('__pycache__','*.zip'))
        (cls.root/'manifests').mkdir()
        shutil.copyfile(ROOT/'manifests/post_dir_integration_004.json',cls.root/'manifests/post_dir_integration_004.json')
        overlay_baseline(ROOT,cls.root)  # Task 037C: authenticated baseline bytes

    def alter(self,path,body):
        file=self.root/path;before=file.read_bytes();self.addCleanup(file.write_bytes,before);file.write_bytes(body)

    def test_complete_current_and_all_previous_resolvers_validate(self):
        from scripts import compiler_capture_observation_amendment as capture
        from scripts import compiler_media_observation_amendment as media
        from scripts import compiler_media_thread_amendment as threads
        from scripts import compiler_media_policy_observation_amendment as policy
        from scripts import compiler_media_source_pin_amendment as pin
        from scripts import compiler_stitch_input_amendment as stitch
        for resolver in (audit,capture,media,threads,policy,pin,stitch):resolver.validate(self.root)

    def test_four_original_git_bytes_and_replacements_authenticated(self):
        self.assertEqual(audit.validate(self.root),self.doc)
        for row in self.doc['replacements']:
            raw=subprocess.check_output(['git','show',self.doc['parent_commit']+':'+row['path']],cwd=ROOT)
            self.assertEqual(raw,(self.root/row['preimage']).read_bytes())
            self.assertEqual(audit.authenticated_previous_bytes(self.root,row['path'],sha256(raw).hexdigest()),raw)

    def test_every_active_replacement_tamper_rejected(self):
        for row in self.doc['replacements']:
            file=self.root/row['path'];before=file.read_bytes()
            try:
                file.write_bytes(before+b'UNAUTHORIZED\n')
                with self.subTest(path=row['path']),self.assertRaises(ValueError):audit.validate(self.root)
            finally:file.write_bytes(before)

    def test_every_original_preimage_tamper_rejected(self):
        for row in self.doc['replacements']:
            file=self.root/row['preimage'];before=file.read_bytes()
            try:
                file.write_bytes(before+b'UNAUTHORIZED\n')
                with self.subTest(path=row['path']),self.assertRaises(ValueError):audit.validate(self.root)
            finally:file.write_bytes(before)

    def test_recomputed_active_hash_cannot_self_bless(self):
        changed=deepcopy(self.doc);row=changed['replacements'][0]
        self.alter(row['path'],b'UNAUTHORIZED\n');row['active_sha256']=sha256(b'UNAUTHORIZED\n').hexdigest();row['active_bytes']=13
        self.alter(audit.DOCUMENT,json.dumps(changed).encode())
        self.assertRaisesRegex(ValueError,'PR_SOURCE_CONTRACT_DOCUMENT',audit.validate,self.root)

    def test_duplicate_extra_or_wildcard_entries_rejected(self):
        file=self.root/audit.DOCUMENT;before=file.read_bytes()
        try:
            for mode in ('duplicate','extra','wildcard'):
                changed=deepcopy(self.doc);row=deepcopy(changed['replacements'][0])
                if mode!='duplicate':row['path']='bie/compiler/**' if mode=='wildcard' else 'bie/compiler/unapproved.py'
                changed['replacements'].append(row);file.write_bytes(json.dumps(changed).encode())
                with self.subTest(mode=mode),self.assertRaises(ValueError):audit.validate(self.root)
        finally:file.write_bytes(before)

    def test_duplicate_document_keys_rejected(self):
        self.alter(audit.DOCUMENT,b'{"schema":"x","schema":"y"}')
        self.assertRaises(ValueError,audit.validate,self.root)

    def test_original_manifest_and_M1_and_parent_seals_immutable(self):
        for name in ('manifests/post_dir_integration_004.json',audit.M1_DOCUMENT,audit.PREVIOUS_DOCUMENT):
            file=self.root/name;before=file.read_bytes()
            try:
                file.write_bytes(before+b' ')
                with self.subTest(path=name),self.assertRaises(ValueError):audit.validate(self.root)
            finally:file.write_bytes(before)

    def test_coordinated_rollback_rejected_by_current_parent_entry(self):
        from scripts import compiler_stitch_input_amendment as stitch
        saved={}
        try:
            for row in self.doc['replacements']:
                file=self.root/row['path'];saved[file]=file.read_bytes();file.write_bytes((self.root/row['preimage']).read_bytes())
            for check in (audit.validate,stitch.validate):self.assertRaises(ValueError,check,self.root)
        finally:
            for file,raw in saved.items():file.write_bytes(raw)

    def test_missing_latest_seal_rejected_not_historical_fallback(self):
        from scripts import compiler_stitch_input_amendment as stitch
        file=self.root/audit.DOCUMENT;before=file.read_bytes()
        try:
            file.unlink()
            for check in (audit.validate,stitch.validate):self.assertRaises(FileNotFoundError,check,self.root)
        finally:file.write_bytes(before)

    def test_unlisted_parent_active_helper_change_rejected(self):
        self.alter('bie/compiler/qa_support/bounded_media_threads.cjs',b'UNAUTHORIZED\n')
        self.assertRaisesRegex(ValueError,'UNLISTED_ACTIVE_BYTES',audit.validate,self.root)

    def test_legacy_cache_active_tamper_code_preserved(self):
        from scripts import compiler_media_policy_observation_amendment as policy
        self.alter(audit.CACHE,b'UNAUTHORIZED\n')
        for check in (audit.validate,policy.validate):
            self.assertRaisesRegex(ValueError,'^COMP_CACHE_AMENDMENT_ACTIVE_BYTES$',check,self.root)

    def test_legacy_paint_active_tamper_code_preserved(self):
        from scripts import compiler_stitch_input_amendment as stitch
        self.alter(audit.PAINT,b'UNAUTHORIZED\n')
        for check in (audit.validate,stitch.validate):
            self.assertRaisesRegex(ValueError,'^COMP_PAINT_AMENDMENT_ACTIVE_BYTES$',check,self.root)

    def test_document_and_preimage_failures_not_blanket_remapped(self):
        self.alter(self.doc['replacements'][0]['preimage'],b'UNAUTHORIZED\n')
        self.assertRaisesRegex(ValueError,'^PR_SOURCE_CONTRACT_PREIMAGE$',audit.validate,self.root)

    def test_foreign_parent_target_or_hash_rejected(self):
        self.assertRaises(ValueError,audit.authenticated_previous_bytes,self.root,'bie/compiler/foreign.py','a'*64)
        self.assertRaises(ValueError,audit.authenticated_previous_bytes,self.root,audit.CACHE,'a'*64)

    def test_original_four_native_M1_sources_remain_identical(self):
        original=json.loads((ROOT/audit.M1_DOCUMENT).read_bytes())
        for row in original['replacements']:
            raw=(ROOT/row['path']).read_bytes().replace(b'\r\n',b'\n')
            self.assertEqual(len(raw),row['active_bytes']);self.assertEqual(sha256(raw).hexdigest(),row['active_sha256'])

    def test_native_unknown_path_still_rejected_by_full_M1_gate(self):
        from scripts import compiler_motion_source_amendment as motion
        file=self.root/'bie/compiler/unapproved.py';file.write_bytes(b'# UNAUTHORIZED\n');self.addCleanup(file.unlink)
        self.assertRaisesRegex(ValueError,'UNEXPECTED_COMPILER_PATH',motion.validate,self.root)

    def test_registration_once_without_native_or_safety_or_inherited_overlap(self):
        from tests.compiler import run_m1_tests as runner
        lanes,inherited=runner.inventory();name='tests/compiler/test_m1_pr_source_contract.py'
        self.assertEqual(lanes['new'].count(name),1);self.assertEqual(len(lanes['native-extra']),214)
        self.assertNotIn(name,lanes['native-extra']);self.assertNotIn(name,lanes['safety']);self.assertNotIn(name,inherited)

if __name__=='__main__':unittest.main()
