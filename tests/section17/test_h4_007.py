import unittest
from copy import deepcopy
from bie.evaluation.benchmarks.browser.replay import compare,normalized
from h4_support import receipt
class H4007(unittest.TestCase):
 def setUp(self):self.a,self.b=receipt()['observed']['runs']
 def test_real_context_replay(self):self.assertTrue(compare(self.a,self.b)['matches'])
 def test_report_stable_identity(self):self.assertEqual(compare(self.a,self.b)['first_sha256'],compare(self.a,self.b)['second_sha256'])
 def test_text_change_detected(self):
  self.b['steps'][0]['observations']['#question']['text']='drift';self.assertFalse(compare(self.a,self.b)['matches'])
 def test_geometry_change_detected(self):
  self.b['steps'][0]['observations']['#question']['bounds']['width']+=1;self.assertFalse(compare(self.a,self.b)['matches'])
 def test_action_removal_detected(self):self.b['steps'].pop();self.assertFalse(compare(self.a,self.b)['matches'])
 def test_fault_not_normalized_away(self):self.b['events']['page_errors']=['error'];self.assertFalse(compare(self.a,self.b)['matches'])
 def test_pixels_reported_separately(self):
  self.b['screenshot']['sha256']='0'*64;r=compare(self.a,self.b);self.assertTrue(r['matches']);self.assertFalse(r['screenshot_bytes_identical'])
 def test_index_not_part_of_observed_equivalence(self):self.b['fresh_context_index']=99;self.assertTrue(compare(self.a,self.b)['matches'])
