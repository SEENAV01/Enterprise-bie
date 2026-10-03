"""Positive preservation plus live tamper controls for one exact cache repair."""
from pathlib import Path
import hashlib,json,os,shutil,tempfile,unittest
from scripts.compiler_cache_source_amendment import resolve,EXPECTED,MANIFEST,MANIFEST_SHA,TARGET,DOCUMENT,BEFORE
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
        for name in (TARGET,DOCUMENT,BEFORE):
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
    def run_gate(self):return resolve(self.root,self.manifest_path,self.manifest)
    def test_original_ledger_unchanged_and_both_producer_versions_hash_bound(self):
        before=self.manifest_path.read_bytes();result,count=self.run_gate()
        self.assertEqual(count,1);self.assertEqual(self.manifest_path.read_bytes(),before)
        self.assertEqual(len(result['members']),len(self.manifest['members']))
        changed=[(a,b) for a,b in zip(self.manifest['members'],result['members']) if a!=b]
        self.assertEqual(len(changed),1);self.assertEqual(changed[0][1]['canonical_path'],BEFORE)
        self.assertEqual(changed[0][0]['canonical_path'],TARGET)
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

def selected_suite():return unittest.defaultTestLoader.loadTestsFromTestCase(CompilerSourceAmendment)
if __name__=='__main__':unittest.main(verbosity=2)
