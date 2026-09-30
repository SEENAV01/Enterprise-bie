import unittest
from copy import deepcopy
from bie.evaluation.benchmarks.browser.scoring import grade
from h4_support import receipt,reference,assert_error
class H4006(unittest.TestCase):
 def setUp(self):self.r=reference();self.o=receipt()['observed']
 def test_correct_path_scores_one(self):self.assertEqual(grade(self.r,self.o)['score_exact'],'1')
 def test_wrong_expected_text_rejected(self):
  self.r['steps'][0]['checks'][0]['expected']='Incorrect goal';self.assertEqual(grade(self.r,self.o)['outcome'],'FAIL')
 def test_missing_steps_not_dropped(self):
  self.o['runs'][0]['steps'].pop();self.assertEqual(grade(self.r,self.o)['outcome'],'FAIL')
 def test_missing_dom_not_credit(self):
  self.o['runs'][0]['steps'][0]['observations']={};self.assertEqual(grade(self.r,self.o)['outcome'],'FAIL')
 def test_console_error_is_failure(self):
  self.o['runs'][0]['events']['console_errors']=['bad'];self.assertEqual(grade(self.r,self.o)['outcome'],'FAIL')
 def test_blocked_request_is_failure(self):
  self.o['runs'][0]['events']['blocked_requests']=['external'];self.assertEqual(grade(self.r,self.o)['outcome'],'FAIL')
 def test_no_learner_efficacy_claim(self):self.assertFalse(grade(self.r,self.o)['objectives'][0]['learner_improvement_verified'])
 def test_no_semantic_claim(self):self.assertFalse(grade(self.r,self.o)['objectives'][0]['semantic_source_entailment_verified'])
 def test_missing_replay_is_blocked(self):
  self.o['runs'].pop();assert_error(self,lambda:grade(self.r,self.o),'BROWSER_REPLAY_INCOMPLETE')
 def test_undefined_contrast_not_pass(self):
  self.o['runs'][0]['steps'][0]['observations']['#question']['contrast_at_least']=None;self.assertEqual(grade(self.r,self.o)['outcome'],'FAIL')
