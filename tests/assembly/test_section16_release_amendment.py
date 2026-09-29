"""Positive and seeded-negative tests for the narrow preservation amendment."""
import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('qa_release_amendment_under_test',
    ROOT / 'scripts/section16_release_amendment.py')
amendment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(amendment)


class ReleaseAmendmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        paths = [amendment.MANIFEST, amendment.LEDGER]
        for entry in amendment.ENTRIES:
            paths.extend((entry['active_path'], entry['before_image']))
        for relative in paths:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        self.rows = list(csv.DictReader(io.StringIO((self.root / amendment.LEDGER).read_text())))

    def mutate_manifest(self, change):
        path = self.root / amendment.MANIFEST
        value = json.loads(path.read_text())
        change(value)
        path.write_text(json.dumps(value))

    def rejected(self, code):
        with self.assertRaisesRegex(ValueError, code):
            amendment.resolve(self.root, self.rows)

    def test_exact_amendment_preserves_original_identity_and_other_rows(self):
        original = copy.deepcopy(self.rows)
        result = amendment.resolve(self.root, self.rows)
        self.assertEqual(self.rows, original)
        self.assertEqual(len(result), len(original))
        affected = {item['file_id']: item for item in amendment.ENTRIES}
        for before, after in zip(original, result):
            if before['file_id'] not in affected:
                self.assertEqual(after, before)
            else:
                self.assertEqual(after['canonical_path'], affected[before['file_id']]['before_image'])
                self.assertEqual(after['disposition'], 'ARCHIVED_EVIDENCE')
                for key in ('file_id', 'sha256', 'bytes', 'archive', 'source_path', 'canonical_sha256'):
                    self.assertEqual(after[key], before[key])

    def test_manifest_is_required(self):
        (self.root / amendment.MANIFEST).unlink()
        self.rejected('MISSING')

    def test_acceptance_claim_is_rejected(self):
        self.mutate_manifest(lambda m: m.update(product_accepted=True))
        self.rejected('IDENTITY')

    def test_section_signoff_claim_is_rejected(self):
        self.mutate_manifest(lambda m: m.update(section_signed_off=True))
        self.rejected('IDENTITY')

    def test_additional_path_is_rejected(self):
        self.mutate_manifest(lambda m: m['entries'].append(dict(m['entries'][0])))
        self.rejected('IDENTITY')

    def test_repointed_before_image_is_rejected(self):
        self.mutate_manifest(lambda m: m['entries'][0].update(before_image='../outside.py'))
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

    def test_changed_original_before_image_is_rejected(self):
        path = self.root / amendment.ENTRIES[0]['before_image']
        path.write_bytes(path.read_bytes() + b'# tamper\n')
        self.rejected('BYTES')

    def test_changed_active_source_is_rejected(self):
        path = self.root / amendment.ENTRIES[0]['active_path']
        path.write_bytes(path.read_bytes() + b'# tamper\n')
        self.rejected('BYTES')

    def test_changed_migrated_assertion_is_rejected(self):
        path = self.root / amendment.ENTRIES[1]['active_path']
        path.write_bytes(path.read_bytes().replace(b'CONTRACT_ONLY', b'SUCCESS'))
        self.rejected('BYTES')

    def test_missing_original_row_is_rejected(self):
        self.rows = [row for row in self.rows if row['file_id'] != amendment.ENTRIES[0]['file_id']]
        self.rejected('COVERAGE')

    def test_duplicated_original_row_is_rejected(self):
        self.rows.append(next(row for row in self.rows if row['file_id'] == amendment.ENTRIES[0]['file_id']))
        self.rejected('COVERAGE')

    def test_original_row_identity_cannot_be_rewritten(self):
        next(row for row in self.rows if row['file_id'] == amendment.ENTRIES[0]['file_id'])['sha256'] = '0' * 64
        self.rejected('ORIGINAL_IDENTITY')


if __name__ == '__main__':
    unittest.main()
