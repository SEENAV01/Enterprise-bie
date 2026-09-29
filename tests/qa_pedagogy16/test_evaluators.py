from ped_helpers import *
from bie.qa.pedagogy_v2.evaluator import verify_reports,evaluate_objectives,evaluate_sequence,evaluate_cognitive_load,evaluate_assessment

class EvaluationTests(FixtureCase):
 def test_reviewed_synthetic_plan_passes_only_local_checks(self):
  x=self.run_check();self.assertEqual(x.status,'CHECKS_PASSED');self.assertFalse(x.product_accepted)
  self.assertEqual(dict(x.sequence.measurements)['routes_checked'],1)
  self.assertEqual(dict(x.assessment.measurements)['structurally_valid_items'],2)
 def test_unsigned_plan_requires_review(self):
  x=evaluate(self.request,self.root,self.policy,as_of=NOW)
  self.assertEqual(x.status,'REVIEW_REQUIRED');self.assertCode(x,'objectives','REVIEW_QUORUM_MISSING')
 def test_modified_source_bytes_block_all_categories(self):
  (self.root/'sources/authored-pedagogy.txt').write_text('tampered')
  x=self.run_check()
  for k in ('objectives','sequence','cognitive_load','assessment'):self.assertEqual(getattr(x,k).status,'BLOCKED')
 def test_modified_output_bytes_block(self):
  (self.root/'outputs/pedagogy-script.txt').write_text('wrong')
  self.assertEqual(self.run_check().status,'BLOCKED')
 def test_missing_output_blocks(self):
  (self.root/'outputs/pedagogy-script.txt').unlink();self.assertEqual(self.run_check().status,'BLOCKED')
 def test_missing_source_blocks(self):
  (self.root/'sources/authored-pedagogy.txt').unlink();self.assertEqual(self.run_check().status,'BLOCKED')
 def test_output_symlink_blocks(self):
  path=self.root/'outputs/pedagogy-script.txt';original=path.read_bytes();path.unlink();outside=self.root/'outside.txt';outside.write_bytes(original);path.symlink_to(outside)
  self.assertEqual(self.run_check().status,'BLOCKED')
 def test_audience_binding(self):self.assertCode(self.run_check(replace(self.request,audience_id='expert')),'objectives','LEARNER_CONTEXT_MISMATCH')
 def test_language_binding(self):self.assertCode(self.run_check(replace(self.request,language='hi')),'objectives','LEARNER_CONTEXT_MISMATCH')
 def test_missing_objective(self):self.assertCode(self.run_check(replace(self.request,objectives=self.request.objectives[1:])),'objectives','OBJECTIVE_SCOPE_MISMATCH')
 def test_missing_segment(self):self.assertCode(self.run_check(replace(self.request,segments=self.request.segments[1:])),'sequence','SEGMENT_SCOPE_MISMATCH')
 def test_missing_route(self):self.assertCode(self.run_check(replace(self.request,routes=())),'sequence','ROUTE_SCOPE_MISMATCH')
 def test_empty_events(self):self.assertCode(self.run_check(replace(self.request,events=())),'cognitive_load','EVENT_INVENTORY_EMPTY')
 def test_empty_teaching(self):self.assertCode(self.run_check(replace(self.request,teachings=())),'objectives','TEACHING_INVENTORY_EMPTY')
 def test_empty_assessments(self):self.assertCode(self.run_check(replace(self.request,items=())),'assessment','ASSESSMENT_INVENTORY_EMPTY')
 def test_unknown_objective_target(self):
  r=replace(self.request,objectives=change(self.request.objectives,'objective_id','obj-1',concept_id='unrelated'))
  self.assertCode(self.run_check(r),'objectives','OBJECTIVE_TARGET_MISMATCH')
 def test_higher_taxonomy_not_automatic_substitution(self):
  r=replace(self.request,objectives=change(self.request.objectives,'objective_id','obj-1',level='CREATE'))
  self.assertCode(self.run_check(r),'objectives','OBJECTIVE_TARGET_MISMATCH')
 def test_missing_objective_criterion(self):
  r=replace(self.request,objectives=change(self.request.objectives,'objective_id','obj-1',criterion_ids=('criterion-1-model',)))
  self.assertCode(self.run_check(r),'objectives','OBJECTIVE_CRITERIA_MISMATCH')
 def test_candidate_cannot_lower_threshold(self):
  r=replace(self.request,objectives=change(self.request.objectives,'objective_id','obj-1',mastery_threshold_ppm=1))
  self.assertCode(self.run_check(r),'objectives','OBJECTIVE_MASTERY_THRESHOLD_MISMATCH')
 def test_objective_missing_statement(self):
  r=replace(self.request,objectives=change(self.request.objectives,'objective_id','obj-1',statement_claim_ids=('absent',)))
  self.assertCode(self.run_check(r),'objectives','OBJECTIVE_EVIDENCE_LINK_MISSING')
 def test_objective_unattached_citation(self):
  r=replace(self.request,objectives=change(self.request.objectives,'objective_id','obj-1',citation_ids=('cite-c2-objective',)))
  self.assertCode(self.run_check(r),'objectives','OBJECTIVE_CITATION_NOT_ATTACHED')
 def test_mention_does_not_teach(self):
  r=replace(self.request,teachings=tuple(replace(t,mode='mention') for t in self.request.teachings))
  self.assertCode(self.run_check(r),'objectives','OBJECTIVE_NOT_TAUGHT')
 def test_practice_does_not_replace_explanation(self):
  r=replace(self.request,teachings=tuple(replace(t,mode='practice') for t in self.request.teachings))
  self.assertCode(self.run_check(r),'objectives','OBJECTIVE_NOT_TAUGHT')
 def test_same_example_id_alias_not_extra_example(self):
  t=self.request.teachings[1];r=replace(self.request,teachings=self.request.teachings+(replace(t,teaching_id='alias-example'),))
  self.assertCode(self.run_check(r,self.spec(minimum_worked_examples=2)),'objectives','WORKED_EXAMPLES_INSUFFICIENT')
 def test_teaching_demand_must_match(self):
  r=replace(self.request,teachings=(replace(self.request.teachings[0],level='REMEMBER'),)+self.request.teachings[1:])
  self.assertCode(self.run_check(r),'objectives','TEACHING_DEPTH_MISMATCH')
 def test_teaching_requires_known_criterion(self):
  r=replace(self.request,teachings=(replace(self.request.teachings[0],criterion_ids=('alien',)),)+self.request.teachings[1:])
  self.assertCode(self.run_check(r),'objectives','TEACHING_CRITERION_UNKNOWN')
 def test_teaching_requires_actual_event(self):
  r=replace(self.request,teachings=(replace(self.request.teachings[0],event_ids=('missing',)),)+self.request.teachings[1:])
  self.assertCode(self.run_check(r),'objectives','TEACHING_EVENT_INVALID')
 def test_prompt_not_explanation(self):
  r=replace(self.request,teachings=(replace(self.request.teachings[0],event_ids=('e1-prompt',)),)+self.request.teachings[1:])
  self.assertCode(self.run_check(r),'objectives','TEACHING_EVENT_ROLE_INVALID')
 def test_teaching_not_cross_segment(self):
  r=replace(self.request,teachings=(replace(self.request.teachings[0],event_ids=('e1-explanation','e2-explanation')),)+self.request.teachings[1:])
  self.assertCode(self.run_check(r),'objectives','TEACHING_EVENT_ROLE_INVALID')
 def test_teaching_not_in_assessment_segment(self):
  r=replace(self.request,segments=change(self.request.segments,'segment_id','instruction-1',kind='assessment'))
  self.assertCode(self.run_check(r),'objectives','TEACHING_SEGMENT_ROLE_INVALID')
 def test_event_requires_segment(self):self.assertCode(self.run_check(self.event('e1-example',segment_id='missing')),'objectives','EVENT_SEGMENT_MISSING')
 def test_event_duration_bound(self):self.assertCode(self.run_check(self.event('e1-example',end_ms=30001)),'sequence','EVENT_OUTSIDE_SEGMENT')
 def test_event_requires_text_span(self):self.assertCode(self.run_check(self.event('e1-example',claim_ids=('missing',))),'objectives','EVENT_CLAIM_MISSING')
 def test_unknown_concept_tags(self):self.assertCode(self.run_check(self.event('e1-example',new_concept_ids=('unknown',))),'cognitive_load','EVENT_CONCEPT_UNKNOWN')
 def test_visible_event_cannot_claim_zero_units(self):
  x=self.run_check(self.event('e1-objective',visual_units=0));self.assertEqual(x.cognitive_load.status,'BLOCKED')
 def test_unscheduled_text_not_ignored(self):
  r=replace(self.request,events=tuple(e for e in self.request.events if e.event_id!='e1-rubric'))
  x=self.run_check(r);self.assertEqual(x.objectives.status,'BLOCKED')
 def test_report_recomputed_not_trusted(self):
  x=self.run_check();self.assertEqual(verify_reports(x,self.request,self.root,self.policy,as_of=NOW,**options(self.request,self.policy)),x)
  with self.assertRaises(ContractError):verify_reports(replace(x,windows=()),self.request,self.root,self.policy,as_of=NOW,**options(self.request,self.policy))
 def test_deterministic_report_and_evidence_order(self):
  x=self.run_check();o=options(self.request,self.policy);o['reviews']=tuple(reversed(o['reviews']))
  y=evaluate(self.request,self.root,self.policy,as_of=NOW,**o)
  self.assertEqual(x.content_digest,y.content_digest)
 def test_standalone_evaluator_wrappers(self):
  x=self.run_check()
  for fn,key in ((evaluate_objectives,'objectives'),(evaluate_sequence,'sequence'),(evaluate_cognitive_load,'cognitive_load'),(evaluate_assessment,'assessment')):
   with self.subTest(category=key):self.assertEqual(fn(self.request,self.root,self.policy,as_of=NOW,**options(self.request,self.policy)),getattr(x,key))
