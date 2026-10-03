"""Positive preservation and live tamper controls for two exact approved repairs."""
from pathlib import Path
import hashlib,json,os,shutil,tempfile,unittest
from scripts.compiler_cache_source_amendment import resolve,EXPECTED,MANIFEST,MANIFEST_SHA,TARGET,DOCUMENT,BEFORE
from scripts.compiler_cache_source_amendment import PAINT_TARGET,PAINT_DOCUMENT,PAINT_BEFORE,PAINT_EXPECTED
from scripts.compiler_cache_source_amendment import resolve_source_members
ROOT=Path(__file__).resolve().parents[2]
class CompilerSourceAmendment(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='bie-s18-compiler-ledger-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        # Standalone source packaging excludes historical ZIP/manifest backups.
        # Local gate supplies the exact canonical ledger read-only; hosted full
        # checkout has it natively. No arbitrary external ledger is accepted.
        source=Path(os.environ.get('BIE_SECTION18_SOURCE_LEDGER',str(ROOT/'manifests'/MANIFEST)))
        raw=source.read_bytes();self.assertEqual(hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest(),MANIFEST_SHA)
        p=self.root/'manifests'/MANIFEST;p.parent.mkdir(parents=True);p.write_bytes(raw);self.manifest_path=p
        self.manifest=json.loads(raw)
        for name in (TARGET,DOCUMENT,BEFORE,PAINT_TARGET,PAINT_DOCUMENT,PAINT_BEFORE):
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
    def run_gate(self):return resolve(self.root,self.manifest_path,self.manifest)
    def test_original_ledger_unchanged_and_both_producer_versions_hash_bound(self):
        before=self.manifest_path.read_bytes();result,count=self.run_gate()
        self.assertEqual(count,2);self.assertEqual(self.manifest_path.read_bytes(),before)
        self.assertEqual(len(result['members']),len(self.manifest['members']))
        changed=[(a,b) for a,b in zip(self.manifest['members'],result['members']) if a!=b]
        self.assertEqual(len(changed),2)
        self.assertEqual({b['canonical_path'] for a,b in changed},{BEFORE,PAINT_BEFORE})
        self.assertEqual({a['canonical_path'] for a,b in changed},{TARGET,PAINT_TARGET})
    def test_arbitrary_producer_replacement_is_rejected(self):
        (self.root/TARGET).write_bytes(b'unsafe arbitrary producer\n')
        with self.assertRaisesRegex(ValueError,'ACTIVE_BYTES'):self.run_gate()
    def test_preimage_tamper_is_rejected(self):
        (self.root/BEFORE).write_bytes(b'CORRUPTED')
        with self.assertRaisesRegex(ValueError,'PREIMAGE'):self.run_gate()
    def test_self_edited_document_hash_cannot_authorize_arbitrary_source(self):
        doc=dict(EXPECTED,replacement_git_lf_sha256=hashlib.sha256(b'arbitrary').hexdigest())
        (self.root/DOCUMENT).write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,'DOCUMENT_IDENTITY'):self.run_gate()
    def test_missing_amendment_is_fail_closed(self):
        (self.root/DOCUMENT).unlink()
        with self.assertRaises(FileNotFoundError):self.run_gate()
    def test_original_manifest_change_is_rejected(self):
        self.manifest_path.write_bytes(self.manifest_path.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_MANIFEST'):self.run_gate()
    def test_duplicate_document_keys_are_rejected(self):
        (self.root/DOCUMENT).write_text('{"schema": "a", "schema": "b"}')
        with self.assertRaisesRegex(ValueError,'DUPLICATE_KEY'):self.run_gate()
    def test_unrelated_manifest_has_no_override(self):
        value=dict(members=[dict(canonical_path='unrelated.py')])
        result,count=resolve(self.root,self.root/'other_integration_001.json',value)
        self.assertIs(result,value);self.assertEqual(count,0)
    def test_extra_original_row_cannot_be_redirected(self):
        selected=next(r for r in self.manifest['members'] if r['canonical_path']==TARGET)
        self.manifest['members'].append(dict(selected))
        with self.assertRaisesRegex(ValueError,'ORIGINAL_ROW'):self.run_gate()

class CompilerPaintAmendment(unittest.TestCase):
    setUp=CompilerSourceAmendment.setUp;run_gate=CompilerSourceAmendment.run_gate
    def test_original_adapted_canonical_and_archive_hashes_are_both_preserved(self):
        before=self.manifest_path.read_bytes();result,count=self.run_gate();self.assertEqual(count,2)
        self.assertEqual(self.manifest_path.read_bytes(),before)
        original=next(r for r in self.manifest['members'] if r['canonical_path']==PAINT_TARGET)
        amended=next(r for r in result['members'] if r['canonical_path']==PAINT_BEFORE)
        for key in ('original_sha256','original_bytes','member','archive','canonical_sha256'):
            self.assertEqual(original[key],amended[key])
        self.assertNotEqual(original['original_sha256'],original['canonical_sha256'])
    def test_arbitrary_active_paint_replacement_is_rejected(self):
        (self.root/PAINT_TARGET).write_bytes(b'unreviewed source\n')
        with self.assertRaisesRegex(ValueError,'COMP_PAINT_AMENDMENT_ACTIVE_BYTES'):self.run_gate()
    def test_paint_preimage_tamper_is_rejected(self):
        (self.root/PAINT_BEFORE).write_bytes(b'changed original')
        with self.assertRaisesRegex(ValueError,'COMP_PAINT_AMENDMENT_PREIMAGE'):self.run_gate()
    def test_self_edited_paint_document_cannot_authorize_arbitrary_source(self):
        (self.root/PAINT_DOCUMENT).write_text(json.dumps(dict(PAINT_EXPECTED,replacement_git_lf_sha256='0'*64)))
        with self.assertRaisesRegex(ValueError,'COMP_PAINT_AMENDMENT_DOCUMENT_IDENTITY'):self.run_gate()
    def test_missing_paint_document_fails_closed(self):
        (self.root/PAINT_DOCUMENT).unlink()
        with self.assertRaises(FileNotFoundError):self.run_gate()
    def test_extra_paint_row_cannot_be_redirected(self):
        row=next(r for r in self.manifest['members'] if r['canonical_path']==PAINT_TARGET)
        self.manifest['members'].append(dict(row))
        with self.assertRaisesRegex(ValueError,'COMP_PAINT_AMENDMENT_ORIGINAL_ROW'):self.run_gate()
    def test_duplicate_paint_document_keys_are_rejected(self):
        (self.root/PAINT_DOCUMENT).write_text('{"schema":"a","schema":"b"}')
        with self.assertRaisesRegex(ValueError,'DUPLICATE_KEY'):self.run_gate()

class CompilerSourceMemberCaller(unittest.TestCase):
    setUp=CompilerSourceAmendment.setUp
    def run_gate(self):return resolve_source_members(self.root,self.manifest_path,self.manifest)
    def test_legacy_caller_preserves_all_original_rows_and_verifies_both_active_replacements(self):
        before=self.manifest_path.read_bytes();rows=self.run_gate()
        self.assertEqual(self.manifest_path.read_bytes(),before)
        self.assertEqual(len(rows),len(self.manifest['source_members']))
        changed=[(a,b) for a,b in zip(self.manifest['source_members'],rows) if a!=b]
        self.assertEqual(len(changed),2)
        self.assertEqual({a['canonical_path'] for a,b in changed},{TARGET,PAINT_TARGET})
        self.assertEqual({b['canonical_path'] for a,b in changed},{BEFORE,PAINT_BEFORE})
        for original,amended in changed:
            self.assertEqual({k:v for k,v in original.items() if k!='canonical_path'},
                             {k:v for k,v in amended.items() if k!='canonical_path'})
            self.assertEqual(hashlib.sha256((self.root/amended['canonical_path']).read_bytes()).hexdigest(),
                             original['canonical_sha256'])
        (self.root/TARGET).write_bytes(b'caller must not skip active producer verification\n')
        with self.assertRaisesRegex(ValueError,'ACTIVE_BYTES'):self.run_gate()
    def test_original_source_hash_override_is_rejected(self):
        next(r for r in self.manifest['source_members'] if r['canonical_path']==TARGET)['canonical_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'SOURCE_MEMBER_INVENTORY'):self.run_gate()
    def test_missing_original_source_row_is_rejected(self):
        self.manifest['source_members']=[r for r in self.manifest['source_members'] if r['canonical_path']!=PAINT_TARGET]
        with self.assertRaisesRegex(ValueError,'SOURCE_MEMBER_INVENTORY'):self.run_gate()
    def test_duplicate_original_source_row_is_rejected(self):
        self.manifest['source_members'].append(dict(next(r for r in self.manifest['source_members'] if r['canonical_path']==TARGET)))
        with self.assertRaisesRegex(ValueError,'SOURCE_MEMBER_INVENTORY'):self.run_gate()
    def test_unrelated_source_redirect_is_rejected(self):
        row=next(r for r in self.manifest['source_members'] if r['canonical_path'] not in (TARGET,PAINT_TARGET))
        row['canonical_path']=BEFORE
        with self.assertRaisesRegex(ValueError,'SOURCE_MEMBER_INVENTORY'):self.run_gate()

class CompilerPreservationCLI(unittest.TestCase):
    """Real CLI/hash seam controls; complete6014-member qualification is hosted.

    The resolver always validates the complete sealed inventory. These focused
    controls select two amended rows plus one actual unchanged source afterward
    to avoid pretending that this small temporary fixture is the full corpus.
    """
    def setUp(self):
        CompilerSourceAmendment.setUp(self)
        from unittest.mock import patch
        from scripts import verify_post_dir
        self.cli=verify_post_dir;self.patch=patch;self.resolver=resolve_source_members
        (self.root/'manifests/post_dir_supplied_inputs.json').write_text(json.dumps(dict(
            files=[],unavailable_declared_archives=[])))
        self.other=None
        for row in self.manifest['source_members']:
            name=row['canonical_path'];path=ROOT/name
            if name not in (TARGET,PAINT_TARGET) and path.is_file():
                raw=path.read_bytes()
                if hashlib.sha256(raw).hexdigest()==row['canonical_sha256']:
                    self.other=name;target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(raw);break
        self.assertIsNotNone(self.other)
    def selected_rows(self,*args):
        # Not a replacement matcher: validate the genuine unchanged sealed
        # ledger, both live replacements and both originals before selecting.
        rows=self.resolver(*args)
        return [row for row in rows if row['canonical_path'] in (BEFORE,PAINT_BEFORE,self.other)]
    def cli_gate(self):
        with self.patch.object(self.cli,'resolve_source_members',side_effect=self.selected_rows) as called:
            result=self.cli.verify(self.root,recursive=False)
            self.assertEqual(called.call_count,1)
        return result
    def test_actual_cli_uses_governed_rows_and_keeps_full_original_inventory(self):
        before=self.manifest_path.read_bytes();result=self.cli_gate()
        self.assertTrue(result['passed'],result['errors']);self.assertEqual(result['errors'],[])
        self.assertEqual(result['source_member_mappings_verified'],6014)
        self.assertEqual(result['unique_paths_hashed'],3)
        self.assertEqual(self.manifest_path.read_bytes(),before)
        self.assertFalse(result['accepted'])
    def test_cli_rejects_unreviewed_active_cache_producer(self):
        (self.root/TARGET).write_bytes(b'unreviewed cache producer\n')
        with self.assertRaisesRegex(ValueError,'COMP_CACHE_AMENDMENT_ACTIVE_BYTES'):self.cli_gate()
    def test_cli_rejects_unreviewed_active_paint_producer(self):
        (self.root/PAINT_TARGET).write_bytes(b'unreviewed paint producer\n')
        with self.assertRaisesRegex(ValueError,'COMP_PAINT_AMENDMENT_ACTIVE_BYTES'):self.cli_gate()
    def test_cli_rejects_original_ledger_tamper(self):
        self.manifest_path.write_bytes(self.manifest_path.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_MANIFEST'):self.cli_gate()
    def test_cli_does_not_skip_unrelated_member_hash_checks(self):
        (self.root/self.other).write_bytes(b'# corrupted unrelated original source\n')
        result=self.cli_gate();self.assertFalse(result['passed'])
        self.assertEqual(result['errors'],['HASH_OR_SIZE_MISMATCH:'+self.other])

def selected_suite():
    return unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls) for cls in
        (CompilerSourceAmendment,CompilerPaintAmendment,CompilerSourceMemberCaller,CompilerPreservationCLI))
if __name__=='__main__':unittest.main(verbosity=2)
