from media_helpers import *
from jsonschema import Draft202012Validator
class SchemaTests(Base):
 def test_structural_schemas_validate_valid_records(self):
  for n in (8,9,10,11):
   c=self.context(n)
   for name,obj in [('job',c.job),({8:'visual',9:'animation',10:'code',11:'game'}[n]+'-policy',c.dp)]+([({10:'code',11:'game'}[n]+'-request',c.bad)] if n>=10 else []):
    with self.subTest(task=n,schema=name):
     sch=json.loads((W/'schemas/qa_section16/batch015'/(name+'.schema.json')).read_text());Draft202012Validator.check_schema(sch);Draft202012Validator(sch).validate(json.loads(canonical_bytes(asdict(obj))))
 def test_schema_rejects_unknown_job_field(self):
  c=self.context();v=json.loads(canonical_bytes(asdict(c.job)));v['accepted']=True;sch=json.loads((W/'schemas/qa_section16/batch015/job.schema.json').read_text());self.assertTrue(list(Draft202012Validator(sch).iter_errors(v)))
 def test_schema_rejects_bool_clock(self):
  c=self.context(9);v=json.loads(canonical_bytes(asdict(c.dp)));v['windows'][0]['start_ms']=True;sch=json.loads((W/'schemas/qa_section16/batch015/animation-policy.schema.json').read_text());self.assertTrue(list(Draft202012Validator(sch).iter_errors(v)))
 def test_cli_preview_only_no_file_changes(self):
  c=self.context();pp=self.home/'policy.json';pp.write_bytes(canonical_bytes(asdict(c.dp)))
  p=subprocess.run([sys.executable,'-B','-m','bie.qa.media_repair_v2',c.task,str(c.root/c.request_ref.path),str(pp),'--root',str(c.root)],cwd=W,capture_output=True,text=True,timeout=10)
  self.assertEqual(p.returncode,3,p.stdout+p.stderr);r=json.loads(p.stdout);self.assertFalse(r['publication_performed']);self.assertFalse(r['product_accepted']);self.assertEqual((c.root/c.target.path).read_bytes(),c.original[c.target.path])
 def test_cli_failure_specific(self):
  c=self.context();p=replace(c.dp,permissions=(replace(c.dp.permissions[0],max_shift_mpx=0),));pp=self.home/'policy.json';pp.write_bytes(canonical_bytes(asdict(p)))
  proc=subprocess.run([sys.executable,'-B','-m','bie.qa.media_repair_v2',c.task,str(c.root/c.request_ref.path),str(pp),'--root',str(c.root)],cwd=W,capture_output=True,text=True,timeout=10)
  self.assertEqual(proc.returncode,2);self.assertEqual(json.loads(proc.stdout)['reason'],'MEDIA_REPAIR_LAYOUT_UNSAT_OR_UNSUPPORTED')
