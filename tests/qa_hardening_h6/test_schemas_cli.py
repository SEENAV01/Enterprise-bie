from h6_helpers import *
import jsonschema
W=Path(__file__).resolve().parents[2]
class SchemasCLI(Temp):
 def test_seven_structural_schemas(self):
  p,b,d=access_fixture(self.root);t,s,bb,doc,src=content_fixture(self.root);tt,ss,bc,o,slots,owned=code_fixture(self.root)
  lp=LeasePolicy();samples={'access-policy':asdict(p),'access-observation':d,'repair-scope':asdict(s),'repair-content':doc,'owned-module':owned,'journal-context':{'binding':asdict(bound(lp)),'policy':asdict(lp)},'corpus-policy':asdict(CorpusPolicy('diagnostic','a'*40,'b'*40,(Suite('unit','tests'),)))}
  for name,sample in samples.items():
   with self.subTest(schema=name):
    schema=json.loads((W/'hardening/section16_h6/schemas'/f'{name}.schema.json').read_text());jsonschema.Draft202012Validator.check_schema(schema);v=jsonschema.Draft202012Validator(schema);sample=json.loads(canonical_bytes(sample));v.validate(sample)
    with self.assertRaises(jsonschema.ValidationError):v.validate({**sample,'unexpected_authority':True})
 def test_readonly_cli_reopens_journal(self):
  p=LeasePolicy();b=bound(p);j=LeaseJournal(self.root/'journal.sqlite',b,p);j.claim('job',digest('effect'),'owner',NOW)
  context=save(self.root,'context.json',dict(binding=asdict(b),policy=asdict(p)));before=j.export()
  r=subprocess.run([sys.executable,'-B','-m','bie.qa.lifecycle_quality_v2',str(j.path),'--context',str(self.root/context.path)],cwd=W,capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stderr+r.stdout);self.assertEqual(json.loads(r.stdout),before);self.assertEqual(j.export(),before)
 def test_cli_missing_journal_does_not_create(self):
  p=LeasePolicy();b=bound(p);c=save(self.root,'context.json',dict(binding=asdict(b),policy=asdict(p)));path=self.root/'missing.sqlite'
  r=subprocess.run([sys.executable,'-B','-m','bie.qa.lifecycle_quality_v2',str(path),'--context',str(self.root/c.path)],cwd=W,capture_output=True,text=True)
  self.assertEqual(r.returncode,2);self.assertFalse(path.exists())
 def test_unknown_journal_context_rejected(self):
  p=LeasePolicy();b=bound(p);j=LeaseJournal(self.root/'journal.sqlite',b,p);j.claim('job',digest('effect'),'owner',NOW)
  c=save(self.root,'context.json',dict(binding=asdict(replace(b,run_id='other')),policy=asdict(p)))
  r=subprocess.run([sys.executable,'-B','-m','bie.qa.lifecycle_quality_v2',str(j.path),'--context',str(self.root/c.path)],cwd=W,capture_output=True,text=True)
  self.assertEqual(r.returncode,2)
 def test_native_code_scope_mandatory(self):
  t,p,b,o,slots,m=code_fixture(self.root);p=replace(p,required_checks=('compile','regression'));b=bound(p)
  self.error('H6_CODE_REVALIDATION_SCOPE',code_proposal,self.root,t,b,p,o,slots)
 def test_review_cannot_drop_required_checks(self):
  t,p,b,d,s=content_fixture(self.root);c=contextual_proposal(self.root,t,b,p,cb(good_generator));c=replace(c,required_checks=('source',))
  self.error('H6_AUTH_CHECK_SCOPE',authorize,c,p,signed(c,p),ReviewVerifier((KEY,)),NOW)
 def test_review_cannot_drop_invalidations(self):
  t,p,b,d,s=content_fixture(self.root);c=contextual_proposal(self.root,t,b,p,cb(good_generator));c=replace(c,invalidates=('source',))
  self.error('H6_AUTH_CHECK_SCOPE',authorize,c,p,signed(c,p),ReviewVerifier((KEY,)),NOW)
 def test_boolean_lease_limit_rejected(self):
  with self.assertRaises(ContractError):LeasePolicy(attempts=True)
 def test_protected_owned_path_collision_rejected(self):
  with self.assertRaises(ContractError):RepairScope('RE',('generated/a.json',),('generated/a.json',),('qa',),('qa',),'generator')

 def test_cli_empty_db_not_misrepresented_as_journal(self):
  p=LeasePolicy();b=bound(p);c=save(self.root,'context.json',dict(binding=asdict(b),policy=asdict(p)));path=self.root/'empty.sqlite';path.write_bytes(b'')
  r=subprocess.run([sys.executable,'-B','-m','bie.qa.lifecycle_quality_v2',str(path),'--context',str(self.root/c.path)],cwd=W,capture_output=True,text=True)
  self.assertEqual(r.returncode,2);self.assertIn('H6_JOURNAL_SCHEMA_MISSING',r.stdout);self.assertEqual(path.read_bytes(),b'')
 def test_cli_corrupt_db_returns_blocked(self):
  p=LeasePolicy();b=bound(p);c=save(self.root,'context.json',dict(binding=asdict(b),policy=asdict(p)));path=self.root/'corrupt.sqlite';path.write_bytes(b'not a database')
  r=subprocess.run([sys.executable,'-B','-m','bie.qa.lifecycle_quality_v2',str(path),'--context',str(self.root/c.path)],cwd=W,capture_output=True,text=True)
  self.assertEqual(r.returncode,2);self.assertEqual(json.loads(r.stdout)['status'],'BLOCKED');self.assertEqual(path.read_bytes(),b'not a database')
