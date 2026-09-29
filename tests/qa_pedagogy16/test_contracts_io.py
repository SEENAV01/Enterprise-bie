from ped_helpers import *
from bie.qa.pedagogy_v2.codec import load_request,load_policy,load_reviews,decode
from bie.qa.pedagogy_v2.scoring import check_mastery_scores
from bie.qa.pedagogy_v2.__main__ import bounded_read
import subprocess,sys,os
import jsonschema
ROOT=Path(__file__).resolve().parents[2]

class ContractTests(FixtureCase):
 def test_request_roundtrip(self):self.assertEqual(load_request(canonical_bytes(asdict(self.request))),self.request)
 def test_policy_roundtrip(self):self.assertEqual(load_policy(canonical_bytes(asdict(self.policy))),self.policy)
 def test_review_roundtrip(self):
  vals=signed_reviews(self.request,self.policy);self.assertEqual(load_reviews(canonical_bytes([asdict(x) for x in vals])),vals)
 def test_unknown_nested_field(self):
  d=json.loads(canonical_bytes(asdict(self.request)));d['events'][0]['trust_me']=True
  with self.assertRaises(ContractError):load_request(canonical_bytes(d))
 def test_wire_strict_types(self):
  base=json.loads(canonical_bytes(asdict(self.request)))
  for name,value in [('events',None),('events',{}),('schema_version',1),('audience_id',False)]:
   with self.subTest(field=name,value=value),self.assertRaises(ContractError):load_request(canonical_bytes({**base,name:value}))
  for value in (False,'100',0.5,None):
   d=json.loads(canonical_bytes(base));d['segments'][0]['duration_ms']=value
   with self.subTest(duration=value),self.assertRaises(ContractError):load_request(json.dumps(d).encode())
 def test_duplicate_json_and_nonfinite_rejected(self):
  for raw in (b'{"source":{},"source":{}}',b'NaN',b'Infinity',b'null',b'[]',b'',b'{',b'\xff'):
   with self.subTest(raw=raw),self.assertRaises(ContractError):load_request(raw)
 def test_path_escape_rejected(self):
  d=json.loads(canonical_bytes(asdict(self.request)));d['source']['outputs'][0]['artifact']['path']='../escape.txt'
  with self.assertRaises(ContractError):load_request(canonical_bytes(d))
 def test_duplicate_objectives_rejected(self):
  with self.assertRaises(ContractError):replace(self.request,objectives=self.request.objectives*2)
 def test_duplicate_event_identity_rejected(self):
  with self.assertRaises(ContractError):replace(self.request,events=self.request.events+(self.request.events[0],))
 def test_event_citation_identity_alias_rejected(self):
  with self.assertRaises(ContractError):replace(self.request,events=(replace(self.request.events[0],event_id='cite-c1-objective'),)+self.request.events[1:])
 def test_reserved_identity_rejected(self):
  with self.assertRaises(ContractError):replace(self.request,segments=(replace(self.request.segments[0],segment_id='load-policy'),)+self.request.segments[1:])
 def test_duplicate_route_segment_rejected(self):
  with self.assertRaises(ContractError):Route('r',('s','s'))
 def test_boolean_numeric_contracts_rejected(self):
  for obj,field in ((self.request.events[0],'visual_units'),(self.request.events[0],'start_ms'),(self.policy.load_limits,'max_motion_units'),(self.policy.objectives[0],'minimum_mastery_items'),(self.policy.objectives[0].criteria[0],'max_points')):
   with self.subTest(field=field),self.assertRaises(ContractError):replace(obj,**{field:True})
 def test_bounds_and_invalid_vocabulary(self):
  cases=((self.request.events[0],'start_ms',-1),(self.request.events[0],'end_ms',0),(self.request.events[0],'kind','arbitrary'),(self.request.segments[0],'kind','unknown'),(self.policy.objectives[0],'minimum_response_ms',0),(self.policy.objectives[0],'minimum_mastery_items',0),(self.policy.objectives[0],'allowed_levels',('UNKNOWN',)),(self.policy.objectives[0].criteria[0],'minimum_points',6),(self.policy.load_limits,'max_text_codepoints_per_minute',0),(self.policy,'minimum_review_confidence_ppm',899999),(self.policy,'minimum_independent_assessors',0))
  for obj,field,value in cases:
   with self.subTest(field=field,value=value),self.assertRaises(ContractError):replace(obj,**{field:value})
 def test_unknown_policy_prerequisite_rejected(self):
  with self.assertRaises(ContractError):self.spec(prerequisites=('unseen',))
 def test_unreachable_policy_segment_rejected(self):
  with self.assertRaises(ContractError):replace(self.policy,expected_segment_ids=self.policy.expected_segment_ids+('hidden',))
 def test_unreachable_policy_objective_rejected(self):
  with self.assertRaises(ContractError):replace(self.policy,routes=(replace(self.policy.routes[0],objective_ids=('obj-1',)),))
 def test_unknown_order_segment_rejected(self):
  with self.assertRaises(ContractError):replace(self.policy,order_constraints=(OrderConstraint('x','missing','instruction-1'),))
 def test_self_order_constraint_rejected(self):
  with self.assertRaises(ContractError):OrderConstraint('x','s','s')
 def test_event_role_collision_rejected(self):
  with self.assertRaises(ContractError):replace(self.request.items[0],solution_event_id='e1-prompt')
 def test_duplicate_rubric_criterion_rejected(self):
  with self.assertRaises(ContractError):replace(self.request.items[0],rubric_points=(('c',1),('c',2)))
 def test_bounded_event_inventory(self):
  es=tuple(Event('x'+str(i),'s',0,1,'action',()) for i in range(1025))
  with self.assertRaises(ContractError):replace(self.request,events=es)
 def test_as_of_boolean_rejected(self):
  with self.assertRaises(ContractError):evaluate(self.request,self.root,self.policy,as_of=True)
 def test_invalid_review_collection(self):
  with self.assertRaises(ContractError):self.run_check(reviews=[])
 def test_invalid_evaluation_types(self):
  with self.assertRaises(ContractError):evaluate(asdict(self.request),self.root,self.policy,as_of=NOW)
 def test_structural_schemas_validate_and_close_fields(self):
  for name,data in [('request',asdict(self.request)),('policy',asdict(self.policy)),('review',asdict(signed_reviews(self.request,self.policy)[0]))]:
   schema=json.loads((ROOT/f'docs/qa_section16/batch006/{name}.schema.json').read_text());data=json.loads(canonical_bytes(data))
   with self.subTest(schema=name):
    jsonschema.Draft202012Validator.check_schema(schema);jsonschema.validate(data,schema)
    with self.assertRaises(jsonschema.ValidationError):jsonschema.validate({**data,'override':True},schema)
 def test_cli_input_size_limit(self):
  p=self.root/'large';p.write_bytes(b'x'*21)
  with self.assertRaises(ContractError):bounded_read(p,20)
 def cli(self,output=None):
  r=self.root/'request.json';p=self.root/'policy.json';r.write_bytes(canonical_bytes(asdict(self.request)));p.write_bytes(canonical_bytes(asdict(self.policy)))
  args=[sys.executable,'-B','-m','bie.qa.pedagogy_v2','--request',str(r),'--policy',str(p),'--artifact-root',str(self.root),'--as-of',str(NOW)]
  if output:args+=['--output',str(output)]
  return subprocess.run(args,cwd=ROOT,capture_output=True,timeout=15)
 def test_unsigned_cli_default(self):
  run=self.cli();self.assertEqual(run.returncode,3);data=json.loads(run.stdout);self.assertEqual(data['status'],'REVIEW_REQUIRED');self.assertFalse(data['product_accepted'])
 def test_cli_output_create_only(self):
  p=self.root/'report.json';p.write_text('PRESERVE');run=self.cli(p);self.assertEqual(run.returncode,4);self.assertEqual(p.read_text(),'PRESERVE')
 def test_cli_writes_actual_report(self):
  p=self.root/'report.json';run=self.cli(p);self.assertEqual(run.returncode,3);self.assertEqual(json.loads(p.read_bytes())['status'],'REVIEW_REQUIRED')
 def test_artifact_hardlink_rejected(self):
  p=self.root/'outputs/pedagogy-script.txt';os.link(p,p.with_name('linked'));self.assertEqual(self.run_check().status,'BLOCKED')

class ScoringTests(FixtureCase):
 def score(self,a,b,spec=None):return check_mastery_scores((('criterion-1-model',a),('criterion-1-total',b)),spec or self.policy.objectives[0])
 def test_threshold_and_floors(self):self.assertTrue(self.score(4,4).passed)
 def test_high_average_cannot_hide_missing_criterion(self):
  s=replace(self.policy.objectives[0],mastery_threshold_ppm=600000);x=self.score(5,2,s)
  self.assertTrue(x.threshold_met);self.assertFalse(x.criterion_floors_met);self.assertFalse(x.passed)
 def test_meeting_floors_not_total_threshold(self):self.assertFalse(self.score(3,3).passed)
 def test_score_is_not_observed_mastery(self):self.assertFalse(self.score(5,5).learner_mastery_observed)
 def test_missing_score(self):
  with self.assertRaises(ContractError):check_mastery_scores((('criterion-1-model',5),),self.policy.objectives[0])
 def test_duplicate_score(self):
  with self.assertRaises(ContractError):check_mastery_scores((('criterion-1-model',5),('criterion-1-model',5)),self.policy.objectives[0])
 def test_out_of_range_score(self):
  for value in (True,-1,6,4.5,'5'):
   with self.subTest(value=value),self.assertRaises(ContractError):self.score(value,5)
 def test_exact_score_property(self):
  for a in range(6):
   for b in range(6):
    with self.subTest(a=a,b=b):self.assertEqual(self.score(a,b).passed,a>=3 and b>=3 and a+b>=8)
