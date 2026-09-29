from media_helpers import *
class CodeTests(Base):
 def test_restore_generated_module(self):
  c=self.context(10);b,w=c.preview();self.assertEqual(b,emit_constants(c.dp));self.assertIn(b'export const total = 6',b);self.assertTrue(w['compile_required'])
 def test_read_only_source(self):
  c=self.context(10);c.preview();self.assertEqual((c.root/c.target.path).read_bytes(),c.original[c.target.path])
 def test_module_identity(self):
  c=self.context(10);self.assertError('MEDIA_REPAIR_MODULE_IDENTITY',c.preview,replace(c.bad,module_id='different'))
 def test_no_handwritten_takeover(self):
  c=self.context(10);a=c.write('generated/other.ts',b'// handwritten\nexport const x=3;','different');self.assertError('MEDIA_REPAIR_UNOWNED_GENERATOR_GRAMMAR',c.preview,replace(c.bad,module=a))
 def test_missing_source_link(self):
  c=self.context(10);self.assertError('MEDIA_REPAIR_CODE_SOURCE_SCOPE',c.preview,p=replace(c.dp,source_claim_ids=('unknown',)))
 def test_unknown_export_identifier(self):
  for name in ('x;evil()','__proto__','class','x.y','eval','1a'):
   with self.subTest(name=name):self.assertError('MEDIA_REPAIR_EXPORT_IDENTIFIER',ExportValue,name,'1')
 def test_proto_key_rejected(self):
  self.assertError('MEDIA_REPAIR_VALUE_KEY',ExportValue,'obj','{"__proto__":{}}')
 def test_integer_precision_guard(self):
  self.assertError('MEDIA_REPAIR_JS_INTEGER_RANGE',ExportValue,'big','9007199254740992')
 def test_floats_not_silently_rounded(self):
  self.assertError('NON_INTEGER_JSON_NUMBER',ExportValue,'n','0.1')
 def test_duplicates_in_json_rejected(self):
  self.assertError('DUPLICATE_JSON_KEY',ExportValue,'n','{"a":1,"a":2}')
 def test_scalar_exports_and_null(self):
  c=self.context(10);p=replace(c.dp,exports=(ExportValue('nothing','null'),ExportValue('flag','true'),ExportValue('label','"six"')));b,_=c.preview(p=p);self.assertIn(b'export const nothing = null;',b)
 def test_executable_text_is_escaped_data(self):
  c=self.context(10);evil='";process.exit(9);//';p=replace(c.dp,exports=(ExportValue('label',json.dumps(evil)),));b,_=c.preview(p=p);self.assertIn(b'\\";process.exit',b)
 def test_stable_export_order(self):
  c=self.context(10);self.assertEqual(emit_constants(c.dp),emit_constants(replace(c.dp,exports=tuple(reversed(c.dp.exports)))))
 def test_no_imports(self):
  c=self.context(10);b,_=c.preview();self.assertNotIn(b'\nimport ',b)
 def test_inspection_does_not_claim_compile(self):
  c=self.context(10);rep=inspect_generated(c.task,c.bad,c.root,c.dp,as_of=NOW);self.assertEqual(rep.status,'BLOCKED');self.assertTrue(any(f.code=='MEDIA_REPAIR_COMPILE_RUNTIME_REVIEW' for f in rep.findings))
 def test_matching_module_still_requires_execution(self):
  c=self.context(10);a=c.write('generated/good.ts',emit_constants(c.dp),'good');rep=inspect_generated(c.task,replace(c.bad,module=a),c.root,c.dp,as_of=NOW);self.assertEqual(rep.status,'REVIEW_REQUIRED')
 def test_actual_tsc_and_node(self):
  c=self.context(10);b,_=c.preview();res=runtime_module(b,10,c.dp);self.assertTrue(res['passed'],res);self.assertEqual(len(res['processes']),2)

class GameTests(Base):
 def test_restore_reducer(self):
  c=self.context(11);b,w=c.preview();self.assertEqual(b,emit_reducer(c.dp.qa));self.assertFalse(w['native_ui_verified'])
 def test_policy_not_modified(self):
  c=self.context(11);before=c.dp.content_digest;c.preview();self.assertEqual(before,c.dp.content_digest)
 def test_wrong_game_identity(self):
  c=self.context(11);self.assertError('MEDIA_REPAIR_GAME_IDENTITY',c.preview,replace(c.bad,game_id='other'))
 def test_all_scenarios_must_resolve(self):
  c=self.context(11);qa=replace(c.dp.qa,transitions=tuple(t for t in c.dp.qa.transitions if not(t.before=='win' and t.action_id=='submit')));self.assertError('MEDIA_REPAIR_ORACLE_SCENARIO_GAP',c.preview,p=GameRepairPolicy(qa))
 def test_learning_states_must_be_reachable(self):
  c=self.context(11);qa=replace(c.dp.qa,transitions=tuple(t for t in c.dp.qa.transitions if t.after!='wrong'));self.assertError('MEDIA_REPAIR_UNREACHABLE_ORACLE_STATE',c.preview,p=GameRepairPolicy(qa))
 def test_correct_feedback_not_invented(self):
  c=self.context(11);qa=c.dp.qa;ss=tuple(replace(s,values=tuple(replace(v,text='Trust me') if v.key=='feedback' else v for v in s.values)) if s.state_id=='win' else s for s in qa.states);self.assertError('MEDIA_REPAIR_GAME_FEEDBACK_SOURCE_MISMATCH',c.preview,p=GameRepairPolicy(replace(qa,states=ss)))
 def test_missing_hint_source(self):
  c=self.context(11);qa=replace(c.dp.qa,text_bindings=(replace(c.dp.qa.text_bindings[0],claim_id='unknown'),)+c.dp.qa.text_bindings[1:]);self.assertError('MEDIA_REPAIR_GAME_SOURCE_SCOPE',c.preview,p=GameRepairPolicy(qa))
 def test_prompt_must_appear(self):
  c=self.context(11);qa=replace(c.dp.qa,learning=(replace(c.dp.qa.learning[0],prompt_claim_id='correct'),));self.assertError('MEDIA_REPAIR_GAME_PROMPT_NOT_PRESENT',c.preview,p=GameRepairPolicy(qa))
 def test_unknown_states_throw_in_generated_code(self):
  c=self.context(11);b,_=c.preview();self.assertIn(b'UNKNOWN_STATE',b);self.assertIn(b'UNDEFINED_TRANSITION',b)
 def test_no_candidate_runtime_oracle_import(self):
  c=self.context(11);b,_=c.preview();self.assertNotIn(b'require(',b);self.assertNotIn(b'from "',b)
 def test_all_states_not_only_happy_path(self):
  c=self.context(11);w=c.preview()[1];self.assertEqual(w['state_count'],6);self.assertEqual(w['transition_count'],14)
 def test_native_ui_and_mastery_not_claimed(self):
  c=self.context(11);w=c.preview()[1];self.assertFalse(w['browser_interaction_verified']);self.assertFalse(w['learner_mastery_observed'])
 def test_deterministic_reducer(self):
  c=self.context(11);self.assertEqual(c.preview(),c.preview())
 def test_actual_tsc_node_all_states_actions(self):
  c=self.context(11);b,_=c.preview();r=runtime_module(b,11,c.dp);self.assertTrue(r['passed'],r);self.assertEqual(len(r['processes']),2)

 def test_prompt_at_response_not_somewhere_else(self):
  c=self.context(11);qa=c.dp.qa;ss=tuple(replace(s,values=tuple(replace(v,text='different question') if v.key=='prompt' else v for v in s.values)) if s.state_id=='three' else s for s in qa.states);self.assertError('MEDIA_REPAIR_GAME_PROMPT_NOT_AT_RESPONSE',c.preview,p=GameRepairPolicy(replace(qa,states=ss)))

 def test_each_response_action_supported(self):
  c=self.context(11);qa=c.dp.qa
  qa=replace(qa,actions=qa.actions+(gh.Action('extra-response','click','#extra',''),),learning=(replace(qa.learning[0],response_action_ids=qa.learning[0].response_action_ids+('extra-response',)),))
  self.assertError('MEDIA_REPAIR_GAME_RESPONSE_NOT_COVERED',c.preview,p=GameRepairPolicy(qa))
