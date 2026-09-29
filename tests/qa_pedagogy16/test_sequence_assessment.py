from ped_helpers import *

class SequenceAssessmentTests(FixtureCase):
 def route(self,*sids):return replace(self.request,routes=(Route('core-route',tuple(sids)),))
 def item(self,**kw):return replace(self.request,items=(replace(self.request.items[0],**kw),)+self.request.items[1:])
 def test_mastery_before_teaching(self):
  r=self.route('assessment-1','instruction-1','instruction-2','assessment-2')
  self.assertCode(self.run_check(r),'sequence','ASSESSMENT_BEFORE_TEACHING')
 def test_prerequisite_taught_later(self):
  r=self.route('instruction-2','assessment-2','instruction-1','assessment-1')
  self.assertCode(self.run_check(r),'sequence','PREREQUISITE_NOT_READY')
 def test_order_constraint_rejected(self):
  r=self.route('instruction-2','instruction-1','assessment-1','assessment-2')
  self.assertCode(self.run_check(r),'sequence','ORDER_CONSTRAINT_VIOLATED')
 def test_order_minimum_spacing(self):
  p=replace(self.policy,order_constraints=(replace(self.policy.order_constraints[0],minimum_gap_ms=20001),))
  self.assertCode(self.run_check(p=p),'sequence','ORDER_CONSTRAINT_VIOLATED')
 def test_order_exact_spacing_passes(self):
  p=replace(self.policy,order_constraints=(replace(self.policy.order_constraints[0],minimum_gap_ms=20000),))
  self.assertEqual(self.run_check(p=p).sequence.status,'CHECKS_PASSED')
 def test_prerequisite_cycle_blocks(self):
  self.assertCode(self.run_check(p=self.spec(prerequisites=('obj-2',))),'sequence','PREREQUISITE_CYCLE')
 def test_order_cycle_blocks(self):
  p=replace(self.policy,order_constraints=self.policy.order_constraints+(OrderConstraint('reverse','instruction-2','instruction-1'),))
  self.assertCode(self.run_check(p=p),'sequence','ORDER_CONSTRAINT_CYCLE')
 def test_omitted_route_segment(self):
  self.assertCode(self.run_check(self.route('instruction-1','assessment-1','instruction-2')),'sequence','ROUTE_MEMBER_MISMATCH')
 def test_route_budget(self):
  p=replace(self.policy,routes=(replace(self.policy.routes[0],max_duration_ms=99999),))
  self.assertCode(self.run_check(p=p),'sequence','ROUTE_DURATION_EXCEEDED')
 def test_route_exact_budget(self):
  p=replace(self.policy,routes=(replace(self.policy.routes[0],max_duration_ms=100000),))
  self.assertEqual(self.run_check(p=p).sequence.status,'CHECKS_PASSED')
 def test_every_branch_is_checked(self):
  r=replace(self.request,routes=self.request.routes+(Route('bad-branch',('instruction-2','assessment-2')),))
  p=replace(self.policy,routes=self.policy.routes+(RouteRequirement('bad-branch',('instruction-2','assessment-2'),('obj-1','obj-2'),100000),))
  x=self.run_check(r,p);self.assertCode(x,'sequence','ROUTE_OBJECTIVE_UNTAUGHT');self.assertCode(x,'sequence','PREREQUISITE_NOT_READY');self.assertCode(x,'assessment','ROUTE_MASTERY_ITEMS_INSUFFICIENT')
 def test_two_valid_branches_checked(self):
  r=replace(self.request,routes=self.request.routes+(Route('second-branch',self.request.routes[0].segment_ids),))
  p=replace(self.policy,routes=self.policy.routes+(replace(self.policy.routes[0],route_id='second-branch'),))
  x=self.run_check(r,p);self.assertEqual(x.status,'CHECKS_PASSED');self.assertEqual(dict(x.sequence.measurements)['routes_checked'],2)
 def test_each_route_requires_distinct_examples(self):
  r=replace(self.request,teachings=tuple(t for t in self.request.teachings if t.teaching_id!='example-1'))
  self.assertCode(self.run_check(r),'sequence','ROUTE_EXAMPLES_INSUFFICIENT')
 def test_retrieval_does_not_replace_application(self):self.assertCode(self.run_check(self.item(level='REMEMBER')),'assessment','ASSESSMENT_DEMAND_MISMATCH')
 def test_wrong_response_mode(self):self.assertCode(self.run_check(self.item(response_mode='choice')),'assessment','ASSESSMENT_DEMAND_MISMATCH')
 def test_missing_transfer(self):self.assertCode(self.run_check(self.item(transfer=False)),'assessment','TRANSFER_REQUIREMENT_MISSING')
 def test_unknown_assessment_objective(self):self.assertCode(self.run_check(self.item(objective_id='unknown')),'assessment','ASSESSMENT_OBJECTIVE_INVALID')
 def test_rubric_must_cover_all_criteria(self):self.assertCode(self.run_check(self.item(criterion_ids=('criterion-1-model',))),'assessment','ASSESSMENT_RUBRIC_MISMATCH')
 def test_rubric_cannot_change_weighting(self):self.assertCode(self.run_check(self.item(rubric_points=(('criterion-1-model',9),('criterion-1-total',1)))),'assessment','ASSESSMENT_RUBRIC_MISMATCH')
 def test_rubric_requires_text(self):self.assertCode(self.run_check(self.item(rubric_claim_ids=('missing',))),'assessment','ASSESSMENT_EVIDENCE_LINK_MISSING')
 def test_missing_answer_event(self):self.assertCode(self.run_check(self.item(solution_event_id='missing')),'assessment','ASSESSMENT_EVIDENCE_LINK_MISSING')
 def test_wrong_event_roles(self):self.assertCode(self.run_check(self.event('e1-prompt',kind='screen')),'assessment','ASSESSMENT_EVENT_ROLE_INVALID')
 def test_cross_segment_answer(self):self.assertCode(self.run_check(self.event('e1-solution',segment_id='assessment-2')),'assessment','ASSESSMENT_EVENT_ROLE_INVALID')
 def test_answer_gate_required(self):self.assertCode(self.run_check(self.event('e1-solution',wait_for_response=False)),'assessment','ANSWER_GATE_MISSING')
 def test_feedback_gate_required(self):self.assertCode(self.run_check(self.event('e1-feedback',wait_for_response=False)),'assessment','ANSWER_GATE_MISSING')
 def test_response_opportunity_required(self):self.assertCode(self.run_check(self.event('e1-solution',start_ms=5999)),'assessment','RESPONSE_TIME_INSUFFICIENT')
 def test_response_time_boundary(self):self.assertEqual(self.run_check(self.event('e1-solution',start_ms=6000)).assessment.status,'CHECKS_PASSED')
 def test_feedback_not_before_answer(self):
  self.assertCode(self.run_check(self.event('e1-solution',start_ms=13000,end_ms=19000)),'assessment','FEEDBACK_BEFORE_SOLUTION')
 def test_exact_answer_span_in_prompt(self):
  self.assertCode(self.run_check(self.event('e1-prompt',claim_ids=('c1-solution',))),'assessment','ANSWER_LEAKAGE')
 def test_second_display_answer_leak(self):
  event=Event('leak','assessment-1',0,5000,'screen',('c1-solution',),(),1)
  r=replace(self.request,events=self.request.events+(event,))
  self.assertCode(self.run_check(r),'assessment','ANSWER_EXPOSED_DURING_RESPONSE')
 def test_duplicate_question_cannot_inflate_count(self):
  r=replace(self.request,items=self.request.items+(replace(self.request.items[0],item_id='alias-question'),))
  self.assertCode(self.run_check(r,self.spec(minimum_mastery_items=2)),'assessment','ROUTE_MASTERY_ITEMS_INSUFFICIENT')
 def test_diagnostic_is_not_mastery(self):self.assertCode(self.run_check(self.item(purpose='diagnostic')),'assessment','ROUTE_MASTERY_ITEMS_INSUFFICIENT')
 def test_formative_is_not_mastery(self):self.assertCode(self.run_check(self.item(purpose='formative')),'assessment','ROUTE_MASTERY_ITEMS_INSUFFICIENT')
