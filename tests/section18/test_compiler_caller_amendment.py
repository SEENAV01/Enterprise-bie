"""H1-011: actual caller guards + strict original/active-source controls."""
from pathlib import Path
import ast,json,os,shutil,tempfile,unittest
from scripts.compiler_caller_source_amendment import ROWS,DOCUMENT,EXPECTED,resolve,resolve_source_members,validate
from scripts.compiler_cache_source_amendment import MANIFEST
ROOT=Path(__file__).resolve().parents[2]
class CallerMaintenanceControls(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='bie-caller-amendment-');self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
  source=Path(os.environ.get('BIE_SECTION18_SOURCE_LEDGER',str(ROOT/'manifests'/MANIFEST)))
  out=self.root/'manifests'/MANIFEST;out.parent.mkdir();shutil.copyfile(source,out)
  self.manifest=json.loads(out.read_bytes());self.path=out
  for name in [DOCUMENT,*[r['path'] for r in ROWS],*[r['preimage'] for r in ROWS]]:
   out=self.root/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,out)
 def test_exact_originals_active_callers_and_all_other_rows_preserved(self):
  before=self.path.read_bytes();result,count=resolve(self.root,self.path,self.manifest)
  self.assertEqual(count,2);self.assertEqual(self.path.read_bytes(),before)
  changed=[(a,b) for a,b in zip(self.manifest['members'],result['members']) if a!=b]
  self.assertEqual(len(changed),2);self.assertEqual({b['canonical_path'] for a,b in changed},{r['preimage'] for r in ROWS})
 def test_active_caller_tamper_rejected(self):
  (self.root/ROWS[0]['path']).write_text('def bypass():return True\n')
  self.assertRaisesRegex(ValueError,'ACTIVE_BYTES',validate,self.root)
 def test_original_caller_tamper_rejected(self):
  (self.root/ROWS[1]['preimage']).write_bytes(b'changed')
  self.assertRaisesRegex(ValueError,'PREIMAGE',validate,self.root)
 def test_self_authorized_hash_rejected(self):
  changed=json.loads(json.dumps(EXPECTED));changed['files'][0]['active_sha256']='0'*64
  (self.root/DOCUMENT).write_text(json.dumps(changed))
  self.assertRaisesRegex(ValueError,'DOCUMENT_IDENTITY',validate,self.root)
 def test_missing_document_fails_closed(self):
  (self.root/DOCUMENT).unlink();self.assertRaises(FileNotFoundError,validate,self.root)
 def test_original_ledger_tamper_rejected(self):
  self.path.write_bytes(self.path.read_bytes()+b' ')
  self.assertRaisesRegex(ValueError,'ORIGINAL_MANIFEST',validate,self.root)
 def test_duplicate_original_row_rejected(self):
  row=next(r for r in self.manifest['members'] if r['canonical_path']==ROWS[0]['path'])
  self.manifest['members'].append(dict(row))
  self.assertRaisesRegex(ValueError,'ORIGINAL_ROW',resolve,self.root,self.path,self.manifest)
 def test_source_member_original_hash_override_rejected(self):
  rows=list(self.manifest['source_members']);rows=[dict(r,canonical_sha256='0'*64) if r['canonical_path']==ROWS[1]['path'] else r for r in rows]
  self.assertRaisesRegex(ValueError,'SOURCE_ROW',resolve_source_members,self.root,self.path,self.manifest,rows)
 def test_original_method_identity_remains27(self):
  import ast
  total=0
  for row in ROWS:
   def ids(raw):return sorted((c.name,n.name) for c in ast.walk(ast.parse(raw)) if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_'))
   old=ids((self.root/row['preimage']).read_bytes());new=ids((self.root/row['path']).read_bytes())
   self.assertEqual(old,new);self.assertEqual(len(new),row['methods']);total+=len(new)
  self.assertEqual(total,27)
if __name__=='__main__':unittest.main(verbosity=2)
