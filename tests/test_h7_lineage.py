import hashlib,json,zipfile
import unittest
from tests.hardening_h6 import test_dsl_traceability as fixtures
from scripts.verify_dsl_traceability import verify,TraceabilityError,ARCHIVE_PREFIX

class H7LineageTests(unittest.TestCase):
    def setUp(self):fixtures.TraceabilityTests.setUp(self)

    def test_forging_current_hash_cannot_approve_changed_code(self):
        path='bie/game_engine/codec.py'
        file=self.root/path;file.write_text('forged')
        row=next(r for r in self.ledger['records'] if r['target']==path)
        row['active_sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
        (self.root/'DSL_TRACEABILITY.json').write_text(json.dumps(self.ledger))
        with self.assertRaisesRegex(TraceabilityError,'ACTIVE_AMENDMENT_HASH'):verify(self.root)

    def test_original_code_cannot_masquerade_as_current_repaired_code(self):
        path='bie/game_engine/codec.py'
        with zipfile.ZipFile(self.root/self.ledger['archive_path']) as archive:
            (self.root/path).write_bytes(archive.read(ARCHIVE_PREFIX+path))
        with self.assertRaisesRegex(TraceabilityError,'RECOVERED_BYTES'):verify(self.root)
