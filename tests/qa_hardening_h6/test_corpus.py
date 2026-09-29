from h6_helpers import *
class Corpus(Temp):
 def init(self,bad=False):self.checkout=self.root/'checkout';self.p=make_repo(self.checkout,bad)
 def test_real_git_case_registration(self):
  self.init();r=register(self.checkout,self.p);self.assertEqual(len(r['cases']),2);self.assertFalse(r['full_repository_tests_executed'])
 def test_registered_tests_execute(self):
  self.init();r=register(self.checkout,self.p);out=execute_registered(self.checkout,self.p,r,approved_digest=r['content_digest']);self.assertTrue(out['all_passed']);self.assertEqual(out['unique_tests'],2);self.assertFalse(out['full_canonical_regression'])
 def test_failed_actual_test_preserved(self):
  self.init(True);r=register(self.checkout,self.p);out=execute_registered(self.checkout,self.p,r,approved_digest=r['content_digest']);self.assertFalse(out['all_passed']);self.assertEqual(out['runs'][0]['failures'],1)
 def test_missing_checkout_not_local_substitute(self):
  self.p=CorpusPolicy('SEENAV01/Enterprise-bie','a'*40,'b'*40,(Suite('tests','tests'),),'CANONICAL_CHECKOUT')
  self.error('H6_CHECKOUT_GIT_REQUIRED',verify_checkout,self.root,self.p)
 def test_wrong_revision_rejected(self):
  self.init();self.error('H6_CHECKOUT_REVISION',verify_checkout,self.checkout,replace(self.p,revision='0'*40))
 def test_wrong_tree_rejected(self):
  self.init();self.error('H6_CHECKOUT_TREE',verify_checkout,self.checkout,replace(self.p,tree='0'*40))
 def test_modified_test_rejected(self):
  self.init();p=self.checkout/'tests/test_case.py';p.write_text(p.read_text()+'\n# changed\n');self.error('H6_CHECKOUT_DIRTY_FILE',verify_checkout,self.checkout,self.p)
 def test_untracked_test_rejected(self):
  self.init();(self.checkout/'tests/test_hidden.py').write_text('');self.error('H6_CHECKOUT_UNTRACKED_FILES',verify_checkout,self.checkout,self.p)
 def test_omitted_test_root_rejected(self):
  self.init();self.error('H6_CORPUS_TEST_SOURCE_CENSUS',verify_checkout,self.checkout,replace(self.p,suites=(Suite('wrong','other'),)))
 def test_overlapping_root_rejected(self):
  self.init();self.error('H6_CORPUS_TEST_SOURCE_CENSUS',verify_checkout,self.checkout,replace(self.p,suites=(Suite('one','tests'),Suite('two','tests'))))
 def test_registration_cannot_remove_case(self):
  self.init();r=register(self.checkout,self.p);approved=r['content_digest'];r['cases'].pop();self.error('H6_CORPUS_APPROVAL_DIGEST',execute_registered,self.checkout,self.p,r,approved_digest=approved)
 def test_wrong_approval_digest(self):
  self.init();r=register(self.checkout,self.p);self.error('H6_CORPUS_APPROVAL_DIGEST',execute_registered,self.checkout,self.p,r,approved_digest='0'*64)
 def test_policy_drift(self):
  self.init();r=register(self.checkout,self.p);self.error('H6_CORPUS_POLICY_CHANGED',execute_registered,self.checkout,replace(self.p,timeout_seconds=61),r,approved_digest=r['content_digest'])
 def test_missing_test_file(self):
  self.init();(self.checkout/'tests/test_case.py').unlink();self.error('H6_CHECKOUT_FILE_BUDGET',verify_checkout,self.checkout,self.p)
 def test_git_source_readonly(self):
  self.init();before=verify_checkout(self.checkout,self.p);r=register(self.checkout,self.p);execute_registered(self.checkout,self.p,r,approved_digest=r['content_digest']);self.assertEqual(before,verify_checkout(self.checkout,self.p))
