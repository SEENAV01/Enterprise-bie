from domain_helpers import *
from bie.qa.pedagogy_v2.models import OrderConstraint,Route,RouteRequirement
class PedagogyTests(Base):
 def test_orders_prerequisites(self):
  c=self.context(6);a,w=pedagogy.repair(c.bad,c.root,c.dp);ids=a.routes[0].segment_ids;self.assertLess(ids.index('instruction-1'),ids.index('instruction-2'))
 def test_teaching_precedes_assessment(self):
  c=self.context(6);a,w=pedagogy.repair(c.bad,c.root,c.dp);ids=a.routes[0].segment_ids
  for n in (1,2):self.assertLess(ids.index('instruction-'+str(n)),ids.index('assessment-'+str(n)))
 def test_response_gates_restored(self):
  c=self.context(6);a,w=pedagogy.repair(c.bad,c.root,c.dp);self.assertTrue(all(e.wait_for_response for e in a.events if e.kind in ('solution','feedback')))
 def test_criteria_never_lowered(self):
  c=self.context(6);a,w=pedagogy.repair(c.bad,c.root,c.dp);self.assertEqual(a.objectives,c.bad.objectives);self.assertEqual(a.items,c.bad.items)
 def test_content_preserved(self):
  c=self.context(6);a,w=pedagogy.repair(c.bad,c.root,c.dp);self.assertEqual(a.source,c.bad.source);self.assertEqual(a.teachings,c.bad.teachings)
 def test_missing_route_not_inserted(self):
  c=self.context(6);self.assertError('DOMAIN_REPAIR_ROUTE_SCOPE',pedagogy.repair,replace(c.bad,routes=()),c.root,c.dp)
 def test_missing_member_not_dropped(self):
  c=self.context(6);r=replace(c.bad,routes=(replace(c.bad.routes[0],segment_ids=c.bad.routes[0].segment_ids[:-1]),));self.assertError('DOMAIN_REPAIR_ROUTE_MEMBERSHIP',pedagogy.repair,r,c.root,c.dp)
 def test_cycle_escalates(self):
  c=self.context(6);p=replace(c.dp,order_constraints=c.dp.order_constraints+(OrderConstraint('reverse','instruction-2','instruction-1'),));self.assertError('DOMAIN_REPAIR_CYCLE',pedagogy.repair,c.bad,c.root,p)
 def test_mentions_not_upgraded(self):
  c=self.context(6);r=replace(c.bad,teachings=tuple(replace(t,mode='mention') for t in c.bad.teachings));self.assertError('DOMAIN_REPAIR_TEACHING_REQUIRED',pedagogy.repair,r,c.root,c.dp)
 def test_duration_guard(self):
  c=self.context(6);p=replace(c.dp,routes=(replace(c.dp.routes[0],max_duration_ms=1),));self.assertError('DOMAIN_REPAIR_ROUTE_DURATION',pedagogy.repair,c.bad,c.root,p)
 def test_spacing_not_invented(self):
  c=self.context(6);p=replace(c.dp,order_constraints=(replace(c.dp.order_constraints[0],minimum_gap_ms=999999),));self.assertError('DOMAIN_REPAIR_REVIEW_SPACING_UNSATISFIED',pedagogy.repair,c.bad,c.root,p)
 def test_response_window_extended(self):
  c=self.context(6);r=replace(c.bad,events=tuple(replace(e,start_ms=3000,end_ms=6000) if e.event_id=='e1-solution' else e for e in c.bad.events));a,w=pedagogy.repair(r,c.root,c.dp);es={e.event_id:e for e in a.events};self.assertGreaterEqual(es['e1-solution'].start_ms-es['e1-prompt'].end_ms,c.dp.objectives[0].minimum_response_ms)
 def test_time_budget(self):
  c=self.context(6);p=replace(c.dp,objectives=tuple(replace(o,minimum_response_ms=30000) for o in c.dp.objectives));self.assertError('DOMAIN_REPAIR_TIME_BUDGET',pedagogy.repair,c.bad,c.root,p,Limits(max_added_ms=0))
 def test_language_mismatch(self):
  c=self.context(6);self.assertError('DOMAIN_REPAIR_AUDIENCE',pedagogy.repair,replace(c.bad,language='hi'),c.root,c.dp)
 def test_all_routes(self):
  c=self.context(6);r=replace(c.bad,routes=c.bad.routes+(Route('branch',tuple(reversed(c.good.routes[0].segment_ids))),));p=replace(c.dp,routes=c.dp.routes+(replace(c.dp.routes[0],route_id='branch'),));a,w=pedagogy.repair(r,c.root,p);self.assertEqual(len(a.routes),2);self.assertEqual(len(w['routes']),2)
 def test_sequence_actual_evaluator(self):
  c=self.context(6);a,w=pedagogy.repair(c.bad,c.root,c.dp);out=evaluate_candidate(c.task,a,c.root,c.dp,as_of=c.now,**options(6,a,c.dp));self.assertEqual(out.sequence.status,'CHECKS_PASSED');self.assertEqual(out.assessment.status,'CHECKS_PASSED')
 def test_deterministic(self):
  c=self.context(6);self.assertEqual(pedagogy.repair(c.bad,c.root,c.dp),pedagogy.repair(c.bad,c.root,c.dp))
 def test_noop(self):
  c=self.context(6);self.assertError('DOMAIN_REPAIR_NO_CHANGE',pedagogy.repair,c.good,c.root,c.dp)
