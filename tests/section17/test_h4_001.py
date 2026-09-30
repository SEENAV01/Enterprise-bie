import unittest
from copy import deepcopy
from dataclasses import replace
from bie.evaluation.benchmarks.browser import contracts as c
from h4_support import reference,candidate,context,assert_error
class H4001(unittest.TestCase):
 def test_reference_valid(self):self.assertEqual(c.reference(reference())['version'],'1.0.0')
 def test_candidate_valid(self):self.assertEqual(len(c.candidate(candidate())['files']),3)
 def test_unknown_candidate_field(self):
  x=candidate();x['passed']=True;assert_error(self,lambda:c.candidate(x))
 def test_boolean_resource_limit(self):assert_error(self,lambda:replace(c.BrowserLimits(),max_steps=True).validate(),'BROWSER_LIMIT_INVALID')
 def test_path_traversal(self):assert_error(self,lambda:c.path('../x.js'),'BROWSER_PATH_INVALID')
 def test_absolute_asset(self):assert_error(self,lambda:c.path('/x.js'),'BROWSER_PATH_INVALID')
 def test_duplicate_casefold_asset(self):
  x=candidate();x['files'].append({**x['files'][0],'path':x['files'][0]['path'].upper()});assert_error(self,lambda:c.candidate(x),'BROWSER_DUPLICATE_PATH')
 def test_manifest_order_identity(self):
  x=candidate();y=deepcopy(x);y['files'].reverse();self.assertEqual(c.content_identity(x),c.content_identity(y))
 def test_label_identity(self):
  x=candidate();y=deepcopy(x);y['origin_kind']='CANONICAL_LAYOUT_UNVERIFIED';self.assertEqual(c.content_identity(x),c.content_identity(y))
 def test_forbid_js_expression_selector(self):assert_error(self,lambda:c.target('body >> script'),'BROWSER_TARGET_INVALID')
 def test_empty_assertions(self):
  x=reference();x['steps'][0]['checks']=[];assert_error(self,lambda:c.reference(x),'BROWSER_EMPTY_CHECKS')
 def test_reference_cannot_claim_golden(self):
  x=reference();x['evidence_grade']='GOLDEN';assert_error(self,lambda:c.reference(x),'BROWSER_UNSUPPORTED_REFERENCE_GRADE')
 def test_missing_objective_mapping(self):
  x=reference();x['objectives'][0]['checks'].pop();assert_error(self,lambda:c.reference(x),'BROWSER_UNMAPPED_CHECKS')
 def test_production_defaults_to_sandbox_request(self):self.assertFalse(c.BrowserExecutionContext('/tmp','/browser','a'*64).allow_unsandboxed_diagnostic)

 def test_reserved_check_id_rejected(self):
  x=reference();x['steps'][0]['checks'][0]['id']='runtime-health';assert_error(self,lambda:c.reference(x),'BROWSER_DUPLICATE_CHECK')
 def test_nonstr_objective_check_rejected(self):
  x=reference();x['objectives'][0]['checks']=[{}];assert_error(self,lambda:c.reference(x),'BROWSER_OBJECTIVE_CHECKS_INVALID')
