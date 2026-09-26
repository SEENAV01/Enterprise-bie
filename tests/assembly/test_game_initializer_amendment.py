from pathlib import Path
import csv,io,json,shutil,tempfile,unittest
from scripts.game_initializer_amendment import resolve,MANIFEST,BEFORE,TARGET,FILE_ID
ROOT=Path(__file__).resolve().parents[2]

class InitializerPreservation(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        for rel in (MANIFEST,BEFORE,TARGET,'manifests/lossless_migration.csv'):
            p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,p)
        self.rows=list(csv.DictReader(io.StringIO((self.root/'manifests/lossless_migration.csv').read_text())))

    def test_one_original_disposition_retained(self):
        result=resolve(self.root,self.rows)
        self.assertEqual(len(result),len(self.rows))
        changed=[(a,b) for a,b in zip(self.rows,result) if a!=b]
        self.assertEqual(len(changed),1)
        self.assertEqual(changed[0][1]['canonical_path'],BEFORE)
        self.assertEqual(changed[0][0]['file_id'],FILE_ID)

    def test_changed_active_exports_rejected(self):
        (self.root/TARGET).write_text('unexpected exports')
        with self.assertRaisesRegex(ValueError,'AMENDMENT_BYTES'):resolve(self.root,self.rows)

    def test_overwritten_original_rejected(self):
        (self.root/BEFORE).write_text('changed original')
        with self.assertRaisesRegex(ValueError,'AMENDMENT_BYTES'):resolve(self.root,self.rows)

    def test_amendment_cannot_redirect_another_component(self):
        p=self.root/MANIFEST;d=json.loads(p.read_text());d['active_path']='bie/director/__init__.py';p.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'AMENDMENT_IDENTITY'):resolve(self.root,self.rows)
