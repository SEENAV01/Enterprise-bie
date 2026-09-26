from pathlib import Path
import json
import shutil
import tempfile
import unittest
from scripts.verify_dsl_traceability import TraceabilityError, confined, verify

ROOT = Path(__file__).resolve().parents[2]

class TraceabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ledger = json.loads((ROOT / 'DSL_TRACEABILITY.json').read_text())
        paths = ['DSL_TRACEABILITY.json', self.ledger['archive_path']]
        paths.extend(r['target'] for r in self.ledger['records'])
        for relative in paths:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def save(self):
        (self.root / 'DSL_TRACEABILITY.json').write_text(json.dumps(self.ledger))

    def test_complete_original_is_recovered(self):
        self.assertEqual(verify(self.root)['records_verified'], 50)

    def test_missing_test_rejected(self):
        (self.root / 'tests/dsl_core/test_codec.py').unlink()
        with self.assertRaisesRegex(TraceabilityError, 'RECOVERED_BYTES'):
            verify(self.root)

    def test_modified_source_rejected(self):
        (self.root / 'bie/game_engine/codec.py').write_text('corrupted')
        with self.assertRaisesRegex(TraceabilityError, 'RECOVERED_BYTES'):
            verify(self.root)

    def test_forged_record_hash_rejected(self):
        self.ledger['records'][0]['sha256'] = '0' * 64
        self.save()
        with self.assertRaisesRegex(TraceabilityError, 'RECORD_HASH'):
            verify(self.root)

    def test_omitted_archive_member_rejected(self):
        self.ledger['records'].pop()
        self.save()
        with self.assertRaisesRegex(TraceabilityError, 'ARCHIVE_COVERAGE'):
            verify(self.root)

    def test_duplicate_member_rejected(self):
        self.ledger['records'].append(self.ledger['records'][0])
        self.save()
        with self.assertRaisesRegex(TraceabilityError, 'ARCHIVE_COVERAGE'):
            verify(self.root)

    def test_archive_tamper_rejected(self):
        archive = self.root / self.ledger['archive_path']
        archive.write_bytes(archive.read_bytes() + b'tampered')
        with self.assertRaisesRegex(TraceabilityError, 'ARCHIVE_HASH'):
            verify(self.root)

    def test_relocated_test_cannot_hide_from_discovery(self):
        row = next(r for r in self.ledger['records'] if r['target'].endswith('test_codec.py'))
        row['target'] = 'lineage/hidden_test_codec.py'
        self.save()
        with self.assertRaisesRegex(TraceabilityError, 'DISPOSITION'):
            verify(self.root)

    def test_extra_test_rejected_as_unreviewed(self):
        (self.root / 'tests/dsl_core/test_injected.py').write_text('')
        with self.assertRaisesRegex(TraceabilityError, 'TEST_DISCOVERY'):
            verify(self.root)

    def test_parent_absolute_and_windows_paths_rejected(self):
        for path in ('../escape', '/escape', 'C:/escape', 'tests\\escape'):
            with self.subTest(path=path), self.assertRaises(TraceabilityError):
                confined(self.root, path)

    def test_product_acceptance_cannot_be_promoted(self):
        self.ledger['product_accepted'] = True
        self.save()
        with self.assertRaisesRegex(TraceabilityError, 'TASK_IDENTITY'):
            verify(self.root)
