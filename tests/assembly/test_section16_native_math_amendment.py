"""Positive and seeded-negative controls for the native parser preservation row."""
import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'native_math_amendment_under_test', ROOT / 'scripts/section16_native_math_amendment.py')
amendment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(amendment)


class NativeMathAmendmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in (amendment.MANIFEST, amendment.LEDGER,
                         amendment.ENTRY['active_path'], amendment.ENTRY['before_image']):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        self.rows = list(csv.DictReader(io.StringIO((self.root / amendment.LEDGER).read_text())))

    def rejected(self, code):
        with self.assertRaisesRegex(ValueError, code):
            amendment.resolve(self.root, self.rows)

    def change_manifest(self, change):
        path = self.root / amendment.MANIFEST
        document = json.loads(path.read_text())
        change(document)
        path.write_text(json.dumps(document))

    def test_exact_amendment_preserves_all_other_rows_and_original_identity(self):
        original = copy.deepcopy(self.rows)
        result = amendment.resolve(self.root, self.rows)
        self.assertEqual(self.rows, original)
        self.assertEqual(len(result), len(original))
        for before, after in zip(original, result):
            if before['file_id'] != amendment.ENTRY['file_id']:
                self.assertEqual(after, before)
            else:
                self.assertEqual(after['canonical_path'], amendment.ENTRY['before_image'])
                self.assertEqual(after['disposition'], 'ARCHIVED_EVIDENCE')
                for key in ('file_id', 'sha256', 'bytes', 'archive', 'source_path', 'canonical_sha256'):
                    self.assertEqual(after[key], before[key])

    def test_missing_manifest_is_rejected(self):
        (self.root / amendment.MANIFEST).unlink()
        self.rejected('MISSING')

    def test_product_acceptance_claim_is_rejected(self):
        self.change_manifest(lambda m: m.update(product_accepted=True))
        self.rejected('IDENTITY')

    def test_section_signoff_claim_is_rejected(self):
        self.change_manifest(lambda m: m.update(section16_signed_off=True))
        self.rejected('IDENTITY')

    def test_unreviewed_scope_is_rejected(self):
        self.change_manifest(lambda m: m['entry'].update(active_path='other.py'))
        self.rejected('IDENTITY')

    def test_wrong_source_archive_hash_is_rejected(self):
        self.change_manifest(lambda m: m.update(source_archive_sha256='0' * 64))
        self.rejected('IDENTITY')

    def test_duplicate_json_key_is_rejected(self):
        path = self.root / amendment.MANIFEST
        value = path.read_text().rstrip()
        path.write_text(value[:-1] + ',"product_accepted": false}')
        self.rejected('DUPLICATE_KEY')

    def test_sealed_ledger_mutation_is_rejected(self):
        path = self.root / amendment.LEDGER
        path.write_bytes(path.read_bytes() + b'\n')
        self.rejected('LEDGER')

    def test_original_before_image_mutation_is_rejected(self):
        path = self.root / amendment.ENTRY['before_image']
        path.write_bytes(path.read_bytes() + b'# tamper\n')
        self.rejected('BYTES')

    def test_active_owner_mutation_is_rejected(self):
        path = self.root / amendment.ENTRY['active_path']
        path.write_bytes(path.read_bytes() + b'# tamper\n')
        self.rejected('BYTES')

    def test_missing_row_is_rejected(self):
        self.rows = [r for r in self.rows if r['file_id'] != amendment.ENTRY['file_id']]
        self.rejected('COVERAGE')

    def test_duplicate_row_is_rejected(self):
        self.rows.append(next(r for r in self.rows if r['file_id'] == amendment.ENTRY['file_id']))
        self.rejected('COVERAGE')

    def test_original_row_identity_mutation_is_rejected(self):
        next(r for r in self.rows if r['file_id'] == amendment.ENTRY['file_id'])['sha256'] = '0' * 64
        self.rejected('ORIGINAL_IDENTITY')

    def test_original_archive_identity_mutation_is_rejected(self):
        next(r for r in self.rows if r['file_id'] == amendment.ENTRY['file_id'])['archive'] = 'other.zip'
        self.rejected('ORIGINAL_IDENTITY')


if __name__ == '__main__':
    unittest.main()
