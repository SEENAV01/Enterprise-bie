import unittest
from copy import deepcopy
from h5_support import *
from bie.evaluation.benchmarks.browser import contracts as old
from bie.evaluation.benchmarks.browser.served import contracts as c
class H5001(unittest.TestCase):
 def test_valid_reference(self):self.assertEqual(c.reference(reference())['schema_version'],c.SCHEMA)
 def test_shared_reference_dispatch(self):self.assertEqual(old.reference(reference()),reference())
 def test_reference_not_mutated(self):r=reference();before=deepcopy(r);c.reference(r);self.assertEqual(r,before)
 def test_unknown_policy_rejected(self):
  r=reference();r['http_policy']['allow_eval']=True;assert_error(self,lambda:c.reference(r))
 def test_missing_policy(self):
  r=reference();del r['http_policy'];assert_error(self,lambda:c.reference(r),'HTTP_POLICY_REQUIRED')
 def test_bool_request_limit(self):
  r=reference();r['http_policy']['max_requests']=True;assert_error(self,lambda:c.reference(r),'HTTP_REQUEST_LIMIT_INVALID')
 def test_empty_assets(self):
  r=reference();r['http_policy']['required_assets']=[];assert_error(self,lambda:c.reference(r),'HTTP_REQUIRED_ASSETS_INVALID')
 def test_duplicate_assets(self):
  r=reference();r['http_policy']['required_assets']*=2;assert_error(self,lambda:c.reference(r),'HTTP_DUPLICATE_REQUIRED_ASSET')
 def test_duplicate_ax_id(self):
  r=reference();r['http_policy']['ax_checks']*=2;assert_error(self,lambda:c.reference(r),'HTTP_DUPLICATE_AX_CHECK')
 def test_reserved_ax_id(self):
  r=reference();r['http_policy']['ax_checks'][0]['id']='http-assets';assert_error(self,lambda:c.reference(r),'HTTP_DUPLICATE_AX_CHECK')
 def test_golden_not_claimed(self):
  r=reference();r['evidence_grade']='GOLDEN';assert_error(self,lambda:c.reference(r))
 def test_entry_required(self):
  r=reference();r['http_policy']['required_assets'].remove('index.html');assert_error(self,lambda:c.binding(r,candidate()),'HTTP_ENTRYPOINT_NOT_REQUIRED')
 def test_undeclared_required_asset(self):
  r=reference();r['http_policy']['required_assets'].append('unknown.js');assert_error(self,lambda:c.binding(r,candidate()),'HTTP_REQUIRED_ASSET_UNDECLARED')
 def test_load_mode_must_match(self):
  x=candidate();x['load_mode']='CLASSIC_SNAPSHOT';assert_error(self,lambda:c.binding(reference(),x),'HTTP_LOAD_MODE_MISMATCH')

 def test_reserved_http_behavior_id(self):
  r=reference();r["steps"][0]["checks"][0]["id"]="http-fake";r["objectives"][0]["checks"][0]="http-fake";assert_error(self,lambda:c.reference(r),"HTTP_RESERVED_BEHAVIOR_ID")
