from domain_helpers import *
from bie.qa.reasoning_v2.logic import Expr
from bie.qa.reasoning_v2.models import Statement,InferenceStep
class ReasoningTests(Base):
 def test_rebuild_support(self):
  c=self.context(5);a,w=reasoning.repair(c.bad,c.root,c.dp);self.assertEqual(a,c.good);self.assertGreater(w['proof_calls'],0)
 def test_preserve_statements_and_evidence(self):
  c=self.context(5);a,w=reasoning.repair(c.bad,c.root,c.dp)
  for f in ('source','statements','evidence','events','masteries','decisions','calibrations'):self.assertEqual(getattr(a,f),getattr(c.bad,f))
 def test_no_new_premise(self):
  c=self.context(5);a,w=reasoning.repair(c.bad,c.root,c.dp);self.assertEqual(a.arguments[0].premise_ids,c.bad.arguments[0].premise_ids)
 def test_invalid_conclusion_not_rewritten(self):
  c=self.context(5);r=replace(c.bad,statements=c.bad.statements[:2]+(replace(c.bad.statements[2],expression=Expr('not','',(c.bad.statements[2].expression,))),));self.assertError('DOMAIN_REPAIR_CONCLUSION_NOT_ENTAILED',reasoning.repair,r,c.root,c.dp)
 def test_inconsistent_roots_rejected(self):
  c=self.context(5);r=replace(c.bad,statements=(c.bad.statements[0],replace(c.bad.statements[1],expression=Expr('not','',(c.bad.statements[0].expression,))),c.bad.statements[2]));self.assertError('DOMAIN_REPAIR_INCONSISTENT_PREMISES',reasoning.repair,r,c.root,c.dp)
 def test_non_deductive_requires_review(self):
  c=self.context(5);r=replace(c.bad,steps=(replace(c.bad.steps[0],method='inductive'),));self.assertError('DOMAIN_REPAIR_NONDEDUCTIVE_REVIEW_REQUIRED',reasoning.repair,r,c.root,c.dp)
 def test_scope_change_rejected(self):
  c=self.context(5);r=replace(c.bad,statements=(replace(c.bad.statements[0],scope='other'),)+c.bad.statements[1:]);self.assertError('DOMAIN_REPAIR_LOGICAL_SCOPE',reasoning.repair,r,c.root,c.dp)
 def test_unknown_step(self):
  c=self.context(5);r=replace(c.bad,arguments=(replace(c.bad.arguments[0],step_ids=('absent',)),));self.assertError('DOMAIN_REPAIR_MISSING_STEP',reasoning.repair,r,c.root,c.dp)
 def test_proof_call_budget(self):
  c=self.context(5);self.assertError('DOMAIN_REPAIR_PROOF_BUDGET',reasoning.repair,c.bad,c.root,c.dp,Limits(max_proof_calls=1))
 def test_total_logic_budget(self):
  c=self.context(5);self.assertError('DOMAIN_REPAIR_TOTAL_LOGIC_BUDGET',reasoning.repair,c.bad,c.root,c.dp,Limits(max_total_logic_visits=1))
 def test_operator_assignment_limit(self):
  c=self.context(5);self.assertError('DOMAIN_REPAIR_LOGIC_RESOURCE_LIMIT',reasoning.repair,c.bad,c.root,replace(c.dp,max_truth_assignments=1))
 def test_operator_atom_limit(self):
  c=self.context(5);self.assertError('DOMAIN_REPAIR_LOGIC_RESOURCE_LIMIT',reasoning.repair,c.bad,c.root,replace(c.dp,max_proof_atoms=1))
 def test_unassigned_step(self):
  c=self.context(5);r=replace(c.bad,steps=c.bad.steps+(replace(c.bad.steps[0],step_id='unused'),));self.assertError('DOMAIN_REPAIR_UNASSIGNED_STEP',reasoning.repair,r,c.root,c.dp)
 def test_policy_argument_scope(self):
  c=self.context(5);self.assertError('DOMAIN_REPAIR_ARGUMENT_SCOPE',reasoning.repair,c.bad,c.root,replace(c.dp,expected_argument_ids=('other',)))
 def test_unsigned_blockers_preserved(self):
  c=self.context(5);g=c.generate();w=json.loads(g.witness);self.assertEqual(w['unsigned_postcheck_status'],'BLOCKED');self.assertTrue(w['open_postcheck_blockers']);self.assertFalse(g.receipt()['product_accepted'])
 def test_actual_legacy_validity_pass(self):
  c=self.context(5);a,w=reasoning.repair(c.bad,c.root,c.dp);out=evaluate_candidate(c.task,a,c.root,c.dp,as_of=c.now,**options(5,a,c.dp));self.assertEqual(out.validity.status,'CHECKS_PASSED')
 def test_noop(self):
  c=self.context(5);self.assertError('DOMAIN_REPAIR_NO_CHANGE',reasoning.repair,c.good,c.root,c.dp)
