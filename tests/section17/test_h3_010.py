import unittest,tempfile,shutil,json,hashlib,os,subprocess,sys
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict,replace
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.adoption.contracts import *
from h3_support import *

from bie.evaluation.benchmarks.adoption.preflight import check,PINS,COMMIT
from bie.evaluation.benchmarks.adoption.__main__ import read
class CanonicalPreflightAndInputTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_actual_pinned_contract_bytes_match(self):
        dest=self.root/'bie/compiler/render_contracts.py';dest.parent.mkdir(parents=True);shutil.copy2(CONTRACT,dest)
        r=check(self.root,expected_commit=COMMIT);contract=next(x for x in r['files'] if x['path'].endswith('render_contracts.py'));self.assertEqual('PIN_MATCH',contract['status']);self.assertEqual('BLOCKED',r['status'])
    def test_missing_checkout_blocked_not_native_success(self):
        r=check(self.root,expected_commit=COMMIT);self.assertEqual('BLOCKED',r['status']);self.assertFalse(r['native_execution_verified']);self.assertFalse(r['section16_integrated'])
    def test_commit_drift_needs_governed_rebase(self):
        with self.assertRaisesRegex(BenchmarkError,'CANONICAL_COMMIT_REBASE_REQUIRED'):check(self.root,expected_commit='0'*40)
    def test_changed_contract_source_blocks(self):
        dest=self.root/'bie/compiler/render_contracts.py';dest.parent.mkdir(parents=True);dest.write_bytes(CONTRACT.read_bytes()+b'\n# changed')
        self.assertIn('CANONICAL_SOURCE_DRIFT',check(self.root,expected_commit=COMMIT)['reasons'])
    def test_all_four_native_file_pins_required(self):self.assertEqual(4,len(PINS));self.assertIn('bie/compiler/artifact_hashing.py',PINS)
    def test_preflight_digest_binds_all_findings(self):
        r=check(self.root,expected_commit=COMMIT);self.assertEqual(digest({k:v for k,v in r.items() if k!='report_sha256'}),r['report_sha256'])
    def test_cli_input_does_not_follow_symlink(self):
        (self.root/'real').write_text('{}');(self.root/'link').symlink_to(self.root/'real')
        with self.assertRaisesRegex(BenchmarkError,'CLI_INPUT_UNSAFE'):read(self.root/'link')
    def test_cli_duplicate_json_keys_rejected(self):
        p=self.root/'r';p.write_text('{"a":1,"a":2}')
        with self.assertRaises(BenchmarkError):read(p)
    def test_cli_nonfinite_number_rejected(self):
        p=self.root/'r';p.write_text('{"a":NaN}')
        with self.assertRaises(BenchmarkError):read(p)
    def test_cli_invalid_encoding_rejected(self):
        p=self.root/'r';p.write_bytes(b'\xff')
        with self.assertRaises(BenchmarkError):read(p)
    def test_cli_size_boundary(self):
        p=self.root/'r';p.write_bytes(b' '*2000001)
        with self.assertRaisesRegex(BenchmarkError,'CLI_JSON_LIMIT'):read(p)
    def test_remaining_dependencies_not_hidden_by_preflight(self):
        r=check(self.root,expected_commit=COMMIT);self.assertIn('PROVISIONED_TRUSTED_NATIVE_RUN',r['remaining']);self.assertFalse(r['product_accepted'])

sys.path.insert(0,str(ROOT/'tools'))
import verify_section17_h3_package as bigpkg
import zipfile
class CumulativeArchiveBoundaryTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def archive(self,items=None):
        z=self.root/'input.zip'
        with zipfile.ZipFile(z,'w') as f:
            for name,data in (items or [('history/parent.zip',b'parent bytes')]):f.writestr(name,data)
        return z
    def test_valid_pinned_outer_archive_extracts(self):
        z=self.archive();r=bigpkg.extract(z,self.root/'out',expected_sha256=bigpkg.sha(z));self.assertEqual('EXTRACTED',r['status']);self.assertFalse(r['recursive_extraction'])
    def test_outer_hash_mismatch_writes_nothing(self):
        z=self.archive()
        with self.assertRaisesRegex(bigpkg.PackageError,'OUTER_ARCHIVE_HASH_MISMATCH'):bigpkg.extract(z,self.root/'out',expected_sha256='0'*64)
        self.assertFalse((self.root/'out').exists())
    def test_per_member_quota_enforced(self):
        z=self.archive()
        with self.assertRaisesRegex(bigpkg.PackageError,'ARCHIVE_SIZE_LIMIT'):bigpkg.extract(z,self.root/'out',expected_sha256=bigpkg.sha(z),max_member_bytes=3,max_total_bytes=100)
    def test_total_quota_enforced(self):
        z=self.archive([('a',b'1234'),('b',b'1234')])
        with self.assertRaisesRegex(bigpkg.PackageError,'ARCHIVE_SIZE_LIMIT'):bigpkg.extract(z,self.root/'out',expected_sha256=bigpkg.sha(z),max_member_bytes=4,max_total_bytes=6)
    def test_path_traversal_is_rejected(self):
        z=self.archive([('../escape',b'data')])
        with self.assertRaises(bigpkg.PackageError):bigpkg.extract(z,self.root/'out',expected_sha256=bigpkg.sha(z))
    def test_case_alias_is_rejected(self):
        z=self.archive([('a',b'1'),('A',b'2')])
        with self.assertRaisesRegex(bigpkg.PackageError,'DUPLICATE_ZIP_MEMBER'):bigpkg.extract(z,self.root/'out',expected_sha256=bigpkg.sha(z))
    def test_file_parent_conflict_is_rejected(self):
        z=self.archive([('a',b'1'),('a/b',b'2')])
        with self.assertRaisesRegex(bigpkg.PackageError,'ZIP_FILE_DIRECTORY_CONFLICT'):bigpkg.extract(z,self.root/'out',expected_sha256=bigpkg.sha(z))
    def test_existing_destination_never_overwritten(self):
        z=self.archive();(self.root/'out').mkdir()
        with self.assertRaisesRegex(bigpkg.PackageError,'DESTINATION_ALREADY_EXISTS'):bigpkg.extract(z,self.root/'out',expected_sha256=bigpkg.sha(z))
    def test_bool_is_not_extraction_budget(self):
        z=self.archive()
        with self.assertRaisesRegex(bigpkg.PackageError,'INVALID_EXTRACTION_LIMIT'):bigpkg.extract(z,self.root/'out',expected_sha256=bigpkg.sha(z),max_member_bytes=True)
    def test_manifest_stream_verify_and_tamper(self):
        p=self.root/'tree';p.mkdir();(p/'a').write_bytes(b'hello');(p/'MANIFEST.json').write_text(json.dumps({'schema_version':'1.0.0','files':{'a':bigpkg.sha(p/'a')}}));self.assertEqual('VERIFIED',bigpkg.verify(p)['status']);(p/'a').write_bytes(b'changed')
        with self.assertRaisesRegex(bigpkg.PackageError,'FILE_HASH_MISMATCH'):bigpkg.verify(p)
