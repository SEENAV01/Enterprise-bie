"""Synthetic protocol transcripts exercise validators; no actual HTTP success claim."""
import unittest
from h5_support import *
from bie.evaluation.benchmarks.browser.served.evidence import validate,grade
class H5007(unittest.TestCase):
 def test_valid_structural_fixture(self):self.assertTrue(validate(reference(),candidate(),synthetic_observed()))
 def test_blocked_has_no_grade(self):
  v=synthetic_observed();v['status']='BLOCKED';assert_error(self,lambda:validate(reference(),candidate(),v),'HTTP_EVIDENCE_INCOMPLETE')
 def test_missing_replay(self):
  v=synthetic_observed();v['runs'].pop();assert_error(self,lambda:validate(reference(),candidate(),v),'HTTP_REPLAY_INCOMPLETE')
 def test_changed_wire_hash(self):
  v=synthetic_observed();v['runs'][0]['http_responses'][0]['sha256']='0'*64;assert_error(self,lambda:validate(reference(),candidate(),v),'HTTP_RESPONSE_BINDING_MISMATCH')
 def test_csp_tampering(self):
  v=synthetic_observed();v['runs'][0]['http_responses'][0]['headers']['content-security-policy']='default-src *';assert_error(self,lambda:validate(reference(),candidate(),v),'HTTP_RESPONSE_HEADERS_MISMATCH')
 def test_mime_tampering(self):
  v=synthetic_observed();v['runs'][0]['http_responses'][0]['headers']['content-type']='text/plain';assert_error(self,lambda:validate(reference(),candidate(),v),'HTTP_RESPONSE_HEADERS_MISMATCH')
 def test_missing_server_response(self):
  v=synthetic_observed();v['runs'][0]['http_server'].pop();assert_error(self,lambda:validate(reference(),candidate(),v),'HTTP_WIRE_SERVER_MISMATCH')
 def test_hidden_readiness_claim(self):
  v=synthetic_observed();v['runs'][0]['readiness'][0]['observed_text']='Unready';assert_error(self,lambda:validate(reference(),candidate(),v),'HTTP_READINESS_EVIDENCE_INVALID')
 def test_missing_ax(self):
  v=synthetic_observed();v['runs'][0]['ax']={};assert_error(self,lambda:validate(reference(),candidate(),v),'HTTP_AX_EVIDENCE_MISSING')
 def test_accounting_false_no_pass(self):
  v=synthetic_observed();v['server_accounting']['requests']=0;assert_error(self,lambda:validate(reference(),candidate(),v),'HTTP_ACCOUNTING_MISMATCH')
 def test_accounting_limit_true_no_pass(self):
  v=synthetic_observed();v['server_accounting']['limit_exceeded']=True;assert_error(self,lambda:validate(reference(),candidate(),v),'HTTP_ACCOUNTING_MISMATCH')
 def test_missing_required_asset_penalty(self):
  v=synthetic_observed();v['runs'][0]['http_responses']=[x for x in v['runs'][0]['http_responses'] if x['path']!='feedback.mjs']
  self.assertEqual(grade(reference(),v)['outcome'],'FAIL')
 def test_wrong_native_role_penalty(self):
  v=synthetic_observed();v['runs'][0]['ax']['native-right-name']['role']='link';self.assertEqual(grade(reference(),v)['outcome'],'FAIL')
 def test_fixed_denominator(self):
  v=synthetic_observed();n=grade(reference(),v)['total_weight'];v['runs'][0]['ax']['native-right-name']['ignored']=True;self.assertEqual(grade(reference(),v)['total_weight'],n)

 def test_none_runs_fail_closed(self):
  v=synthetic_observed();v['runs']=None;assert_error(self,lambda:validate(reference(),candidate(),v),'HTTP_REPLAY_INCOMPLETE')
 def test_float_status_not_coerced(self):
  v=synthetic_observed();v['runs'][0]['http_responses'][0]['status']=200.0;assert_error(self,lambda:validate(reference(),candidate(),v),'HTTP_WIRE_TYPE_INVALID')
 def test_boolean_replay_index_not_coerced(self):
  v=synthetic_observed();v['runs'][0]['fresh_context_index']=False;assert_error(self,lambda:validate(reference(),candidate(),v),'HTTP_READINESS_EVIDENCE_INVALID')
