"""Positive and seeded negative controls for the sole governed graph ledger row."""
import copy
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"scripts"))
import task031_graph_amendment as amendment


class PreservationTests(unittest.TestCase):
    def test_legacy_checkout_bytes_pinned(self):
        self.assertIn('/bie/infrastructure/execution_graph_v1.py -text',
            (ROOT/'.gitattributes').read_text().splitlines())

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        for name in (amendment.LEDGER,amendment.OLD,amendment.ACTIVE,"manifests/task031_graph_migration.json"):
            dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
        self.rows=list(csv.DictReader(io.StringIO((self.root/amendment.LEDGER).read_text())))
    def reject(self):
        with self.assertRaises(ValueError):amendment.resolve(self.root,self.rows)
    def test_exact_row_only(self):
        old=copy.deepcopy(self.rows);new=amendment.resolve(self.root,self.rows);self.assertEqual(old,self.rows)
        self.assertEqual(sum(a!=b for a,b in zip(old,new)),1)
        for a,b in zip(old,new):
            if a["file_id"]==amendment.FILE_ID:
                self.assertEqual(b["canonical_path"],amendment.OLD)
                for key in ("sha256","canonical_sha256","bytes","archive","file_id"):self.assertEqual(a[key],b[key])
    def test_sealed_ledger_tamper(self):
        p=self.root/amendment.LEDGER;p.write_bytes(p.read_bytes()+b"\n");self.reject()
    def test_legacy_bytes_tamper(self):(self.root/amendment.OLD).write_bytes(b"tamper");self.reject()
    def test_active_code_tamper(self):(self.root/amendment.ACTIVE).write_bytes(b"tamper");self.reject()
    def test_missing_row(self):self.rows=[r for r in self.rows if r["file_id"]!=amendment.FILE_ID];self.reject()
    def test_duplicate_row(self):self.rows.extend(r.copy() for r in list(self.rows) if r["file_id"]==amendment.FILE_ID);self.reject()
    def test_foreign_original_identity(self):
        next(r for r in self.rows if r["file_id"]==amendment.FILE_ID)["bytes"]="1";self.reject()
    def test_acceptance_forgery(self):
        p=self.root/"manifests/task031_graph_migration.json";m=json.loads(p.read_text());m["product_accepted"]=True;p.write_text(json.dumps(m));self.reject()
    def test_duplicate_manifest_key(self):
        p=self.root/"manifests/task031_graph_migration.json";p.write_text(p.read_text().rstrip()[:-1]+',"product_accepted":false}');self.reject()
    def test_other_rows_unchanged(self):
        result=amendment.resolve(self.root,self.rows)
        self.assertEqual([r for r in result if r["file_id"]!=amendment.FILE_ID],[r for r in self.rows if r["file_id"]!=amendment.FILE_ID])


if __name__=="__main__":unittest.main()
