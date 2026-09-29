from h6_helpers import *
class SourceRepair(Temp):
 def test_native_multiregion_regeneration(self):
  sr,tr,p,b,dp,good,bad=source_fixture(self.root);old=read(self.root,tr);c=source_proposal(self.root,sr,tr,b,p)
  self.assertEqual(strict_json(c.payload),good);self.assertGreaterEqual(c.witness['region_count'],2);self.assertEqual(read(self.root,tr),old)
 def test_missing_source_condition_escalates(self):
  sr,tr,p,b,dp,good,bad=source_fixture(self.root)
  self.error('H6_SOURCE_REEXTRACTION_FAILED',source_proposal,self.root,sr,tr,b,p,required_fragments=((1,'an absent source condition'),))
 def test_preserves_raw_source(self):
  sr,tr,p,b,dp,good,bad=source_fixture(self.root);old=read(self.root,sr);source_proposal(self.root,sr,tr,b,p);self.assertEqual(read(self.root,sr),old)
 def test_no_change_no_proposal(self):
  sr,tr,p,b,dp,good,bad=source_fixture(self.root);tr=save(self.root,tr.path,good,aid=tr.artifact_id)
  self.error('H6_NO_CHANGE',source_proposal,self.root,sr,tr,b,p)
 def test_foreign_source(self):
  sr,tr,p,b,dp,good,bad=source_fixture(self.root);bad['source']['sha256']='0'*64;tr=save(self.root,tr.path,bad,aid=tr.artifact_id)
  self.error('H6_DERIVED_SOURCE_IDENTITY',source_proposal,self.root,sr,tr,b,p)
 def test_foreign_run(self):
  sr,tr,p,b,dp,good,bad=source_fixture(self.root);bad['binding']['run_id']='foreign';tr=save(self.root,tr.path,bad,aid=tr.artifact_id)
  self.error('NATIVE_BINDING_MISMATCH',source_proposal,self.root,sr,tr,b,p)
 def test_wrong_policy_binding(self):
  sr,tr,p,b,dp,good,bad=source_fixture(self.root);self.error('H6_POLICY_BINDING',source_proposal,self.root,sr,tr,replace(b,policy_digest='0'*64),p)
 def test_page_budget_enforced(self):
  sr,tr,p,b,dp,good,bad=source_fixture(self.root)
  with self.assertRaises(ContractError):source_proposal(self.root,sr,tr,b,p,document_policy=DocumentPolicy(max_regions=1))
 def test_source_tampering_rejected(self):
  sr,tr,p,b,dp,good,bad=source_fixture(self.root);(self.root/sr.path).write_bytes(b'changed')
  with self.assertRaises(ContractError):source_proposal(self.root,sr,tr,b,p)
 def test_unregistered_provider_rejected(self):
  sr,tr,p,b,dp,good,bad=source_fixture(self.root);self.error('H6_SOURCE_PROVIDER',source_proposal,self.root,sr,tr,b,p,provider=lambda x:x)

class ContextRepair(Temp):
 def setup_content(self):self.t,self.p,self.b,self.doc,self.src=content_fixture(self.root)
 def gen(self,fn=good_generator):return contextual_proposal(self.root,self.t,self.b,self.p,cb(fn))
 def test_actual_pinned_generator(self):
  self.setup_content();c=self.gen();self.assertIn('is five',c.payload.decode());self.assertTrue(c.witness['generation']['worker_executed']);self.assertEqual(read(self.root,self.t),canonical_bytes(self.doc))
 def test_required_invalidation_preserved(self):
  self.setup_content();c=self.gen();self.assertEqual(c.invalidates,self.p.invalidates);self.assertIn('regression',c.required_checks)
 def test_no_change_escalates(self):
  self.setup_content();self.error('H6_NO_CHANGE',self.gen,no_change_generator)
 def test_condition_omission(self):
  self.setup_content();self.error('H6_CONTEXT_CONDITION_ERASED',self.gen,drops_condition)
 def test_objective_mutation(self):
  self.setup_content();self.error('H6_CONTEXT_PROTECTED_MEANING',self.gen,invents_objective)
 def test_extra_record(self):
  self.setup_content();self.error('H6_CONTEXT_OBJECTIVE_OR_RECORD_LOSS',self.gen,adds_record)
 def test_prompt_authority_payload_rejected(self):
  self.setup_content();self.error('H6_CONTENT_FIELDS',self.gen,authority_output)
 def test_exception_not_success(self):
  self.setup_content();self.error('H6_CONTEXT_GENERATION_FAILED',self.gen,raises_generator)
 def test_unsigned_proposal_is_unapproved(self):
  self.setup_content();c=self.gen();self.error('H6_FRESH_REVIEW_REQUIRED',authorize,c,self.p,None,ReviewVerifier(),NOW)
 def test_fresh_review_authenticated(self):
  self.setup_content();c=self.gen();self.assertTrue(authorize(c,self.p,signed(c,self.p),ReviewVerifier((KEY,)),NOW))
 def test_self_approval_rejected(self):
  self.setup_content();c=self.gen();k=replace(KEY,independence_group=self.p.generator_group)
  self.error('H6_SELF_APPROVAL',authorize,c,self.p,signed(c,self.p,k),ReviewVerifier((k,)),NOW)
 def test_old_review_cannot_approve_new_bytes(self):
  self.setup_content();c=self.gen();review=signed(c,self.p);changed=replace(c,payload=c.payload+b' ')
  self.error('H6_FRESH_REVIEW_REQUIRED',authorize,changed,self.p,review,ReviewVerifier((KEY,)),NOW)
 def test_rejected_assessment_blocks(self):
  self.setup_content();c=self.gen();self.error('H6_FRESH_REVIEW_REQUIRED',authorize,c,self.p,signed(c,self.p,verdict='REJECTED'),ReviewVerifier((KEY,)),NOW)
 def test_expired_assessment_blocks(self):
  self.setup_content();c=self.gen();self.error('H6_FRESH_REVIEW_REQUIRED',authorize,c,self.p,signed(c,self.p,now=NOW-500),ReviewVerifier((KEY,)),NOW)
 def test_source_change_blocks(self):
  self.setup_content();(self.root/self.src.path).write_bytes(b'changed')
  with self.assertRaises(ContractError):self.gen()

class CodeRepair(Temp):
 def setup_code(self):self.t,self.p,self.b,self.o,self.slots,self.manifest=code_fixture(self.root)
 def gen(self):return code_proposal(self.root,self.t,self.b,self.p,self.o,self.slots)
 def update_manifest(self):self.o=save(self.root,self.o.path,self.manifest,aid=self.o.artifact_id)
 def test_owned_complete_literal_repair(self):
  self.setup_code();c=self.gen();self.assertIn(b'total = 5;',c.payload);self.assertIn(b'unit = "items";',c.payload);self.assertTrue(c.witness['native_runtime_required'])
 def test_original_module_unchanged(self):
  self.setup_code();old=read(self.root,self.t);self.gen();self.assertEqual(old,read(self.root,self.t))
 def test_literal_string_escaped(self):
  self.setup_code();self.slots=(replace(self.slots[0],value_json=json.dumps('"; throw Error("bad"); //')),);c=self.gen();self.assertIn(b'\\"',c.payload)
 def test_unknown_slot(self):
  self.setup_code();self.slots=(replace(self.slots[0],slot_id='unknown'),);self.error('H6_UNOWNED_SLOT',self.gen)
 def test_wrong_owner(self):
  self.setup_code();self.manifest['owner']='GAME';self.update_manifest();self.error('H6_MODULE_OWNERSHIP',self.gen)
 def test_wrong_module_hash(self):
  self.setup_code();self.manifest['module']['sha256']='0'*64;self.update_manifest();self.error('H6_MODULE_OWNERSHIP',self.gen)
 def test_slot_hash_changed(self):
  self.setup_code();self.slots=(replace(self.slots[0],before_sha256='0'*64),);self.error('H6_SLOT_POLICY_CHANGED',self.gen)
 def test_overlapping_slots(self):
  self.setup_code();self.slots=(self.slots[0],replace(self.slots[0],slot_id='second'));self.manifest['slots'].append({k:v for k,v in asdict(self.slots[1]).items() if k!='value_json'});self.update_manifest();self.error('H6_SLOT_OVERLAP_OR_BOUNDS',self.gen)
 def test_protected_policy_path(self):
  with self.assertRaises(ContractError):scope('policy/settings.json')
 def test_numeric_substring_is_not_slot(self):
  self.setup_code();raw=read(self.root,self.t).replace(b'total = 6',b'total = 66');self.t=save(self.root,self.t.path,raw,aid=self.t.artifact_id);self.manifest['module']=asdict(self.t);self.update_manifest();self.error('H6_SLOT_NOT_COMPLETE_LITERAL',self.gen)
 def test_handwritten_function_escalates(self):
  self.setup_code();raw=read(self.root,self.t)+b'function handwritten() { return 1; }\n';self.t=save(self.root,self.t.path,raw,aid=self.t.artifact_id);self.manifest['module']=asdict(self.t);self.update_manifest();self.error('H6_UNSUPPORTED_GENERATED_GRAMMAR',self.gen)
 def test_emitter_changed(self):
  self.setup_code();(self.root/self.manifest['emitter']['path']).write_bytes(b'changed')
  with self.assertRaises(ContractError):self.gen()
 def test_no_change(self):
  self.setup_code();self.slots=(replace(self.slots[0],value_json='6'),);self.error('H6_NO_CHANGE',self.gen)
 def test_prototype_key_rejected(self):
  self.setup_code()
  with self.assertRaises(ContractError):replace(self.slots[0],value_json='{"__proto__":1}')
 def test_js_precision_rejected(self):
  self.setup_code()
  with self.assertRaises(ContractError):replace(self.slots[0],value_json='9007199254740993')
