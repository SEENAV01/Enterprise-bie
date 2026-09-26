"""Canonical layout retains and verifies the original isolated package bytes."""
from pathlib import Path
import json,shutil,tempfile,unittest
from scripts.verify_dsl_traceability import TraceabilityError,verify

ROOT=Path(__file__).resolve().parents[2]

class CanonicalTraceabilityTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.ledger=json.loads((ROOT/'DSL_TRACEABILITY.json').read_text())
        for rel in ['DSL_TRACEABILITY.json',self.ledger['archive_path'],*[r['target'] for r in self.ledger['records']]]:
            p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,p)
        self.row=next(r for r in self.ledger['records'] if r['archive_member'].endswith('/bie/__init__.py'))

    def test_archived_package_initializer_tamper_rejected(self):
        self.assertTrue(verify(self.root)['traceability_passed'])
        (self.root/self.row['target']).write_bytes(b'changed original')
        with self.assertRaisesRegex(TraceabilityError,'RECOVERED_BYTES_MISMATCH'):
            verify(self.root)

    def test_original_cannot_be_rebound_to_canonical_shared_package(self):
        self.row['target']='bie/__init__.py'
        self.row['disposition']='existing_active_source_byte_identical'
        (self.root/'DSL_TRACEABILITY.json').write_text(json.dumps(self.ledger))
        with self.assertRaisesRegex(TraceabilityError,'DISPOSITION_MISMATCH'):
            verify(self.root)
