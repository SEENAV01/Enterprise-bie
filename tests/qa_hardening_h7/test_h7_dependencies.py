from h7_helpers import *
import copy
class Dependencies(Temp):
 def setUp(self):super().setUp();self.p,self.r=dependency_fixture(self.root/'dep');self.d=self.root/'dep'
 def call(self,p=None,r=None,now=NOW):
  p=p or self.p;r=r or self.r;return verify_dependencies(self.d,p,r,approved_review_digest=digest(r),now=now)
 def test_actual_metadata(self):self.assertEqual(self.call()['status'],'REVIEW_REQUIRED')
 def test_tamper_module(self):
  (self.d/'package/value.txt').write_text('43');self.error('H7_INSTALLED_BYTE_DRIFT',self.call)
 def test_extra_file(self):
  (self.d/'new.py').write_text('x');self.error('H7_INSTALLED_BYTE_DRIFT',self.call)
 def test_missing_file(self):
  (self.d/'package/value.txt').unlink();self.error('H7_INSTALLED_BYTE_DRIFT',self.call)
 def test_wrong_version(self):
  p=replace(self.p,packages=({**self.p.packages[0],'version':'2.0'},));self.error('H7_INSTALLED_VERSION_DRIFT',self.call,p)
 def test_missing_review(self):
  r={**self.r,'packages':[]};self.error('H7_REVIEW_CENSUS',self.call,r=r)
 def test_duplicate_review(self):
  r={**self.r,'packages':self.r['packages']*2};self.error('H7_REVIEW_CENSUS',self.call,r=r)
 def test_review_future(self):self.error('H7_REVIEW_STALE',self.call,r={**self.r,'created_at':NOW+1})
 def test_review_expired(self):self.error('H7_REVIEW_STALE',self.call,now=NOW+1000)
 def test_review_max_age(self):self.error('H7_REVIEW_STALE',self.call,r={**self.r,'created_at':NOW-86401})
 def test_review_binding(self):self.error('H7_REVIEW_BINDING',self.call,r={**self.r,'policy_digest':'d'*64})
 def test_review_authority(self):self.error('H7_REVIEW_AUTHORITY_DIGEST',verify_dependencies,self.d,self.p,self.r,approved_review_digest='e'*64,now=NOW)
 def test_affected(self):
  r=copy.deepcopy(self.r);r['packages'][0].update(status='AFFECTED',advisory_ids=['SYNTHETIC-001']);self.assertEqual(self.call(r=r)['status'],'BLOCKED')
 def test_unknown_ranges_not_cleared(self):
  r=copy.deepcopy(self.r);r['packages'][0]['status']='UNKNOWN';self.assertEqual(self.call(r=r)['unknown_packages'],['dep'])
 def test_affected_without_advisory(self):
  r=copy.deepcopy(self.r);r['packages'][0]['status']='AFFECTED';self.error('H7_ADVISORY_EVIDENCE',self.call,r=r)
 def test_reference_version(self):
  r=copy.deepcopy(self.r);r['packages'][0]['version']='2';self.error('H7_REVIEW_VERSION',self.call,r=r)
 def test_unresolved(self):
  with self.assertRaises(ContractError):replace(self.p,packages=({**self.p.packages[0],'dependencies':['absent']},))
 def test_file_double_owned(self):
  with self.assertRaises(ContractError):replace(self.p,file_rows=self.p.file_rows+self.p.file_rows)
 def test_unowned_file(self):
  with self.assertRaises(ContractError):replace(self.p,packages=({**self.p.packages[0],'paths':['package/METADATA']},))
 def npm(self,scripts=None):
  data={'name':'diag','version':'1.0','scripts':scripts or {}};(self.d/'package/METADATA').write_bytes(canonical_bytes(data))
  p=replace(self.p,file_rows=tuple(inventory(self.d)),packages=({**self.p.packages[0],'ecosystem':'npm','name':'diag'},));r={**self.r,'policy_digest':p.content_digest};return p,r
 def test_npm(self):p,r=self.npm();self.assertTrue(self.call(p,r)['installed_bytes_verified'])
 def test_npm_unapproved_script(self):
  p,r=self.npm({'postinstall':'node install.js'});self.error('H7_UNAPPROVED_INSTALL_SCRIPT',self.call,p,r)
 def test_npm_explicit_script(self):
  p,r=self.npm({'build':'tsc'});p=replace(p,allowed_scripts=(('dep','build','tsc'),));r={**r,'policy_digest':p.content_digest};self.assertTrue(self.call(p,r)['installed_bytes_verified'])
 def test_osv_match(self):self.assertEqual(review_osv_exact([{'id':'SYNTHETIC','affected':[{'package':{'name':'a'},'versions':['1']}]}],'a','1')['status'],'AFFECTED')
 def test_osv_unknown_range(self):self.assertEqual(review_osv_exact([{'id':'SYNTHETIC','affected':[{'package':{'name':'a'},'ranges':[{'type':'SEMVER'}]}]}],'a','1')['status'],'UNKNOWN')
 def test_osv_withdrawn(self):self.assertEqual(review_osv_exact([{'id':'SYNTHETIC','withdrawn':'date'}],'a','1')['status'],'NO_EXPLICIT_MATCH')
 def test_osv_no_match_not_clearance(self):self.assertFalse(review_osv_exact([],'a','1')['clearance'])
