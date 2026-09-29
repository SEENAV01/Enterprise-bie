from h6_helpers import *
W=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(W/'tests/qa_repair16'))
import repair_helpers as rh
from bie.qa.repair_v2.planner import check_closure
from bie.qa.repair_v2.controller import execute
class Handoff(Temp):
 def setup_change(self):
  self.f=rh.Fixture();self.f.setUp();self.addCleanup(self.f.tearDown)
  checks,invalid=check_closure(self.f.policy,'MATH')
  self.p=RepairScope('MATH',('generated/lesson.txt',),('sources/book.txt',),checks,invalid,'generator-test-group')
  self.b=Binding(self.f.snapshot.run_id,self.f.snapshot.revision,self.f.snapshot.content_digest,self.p.content_digest)
  self.c=make_change('BIE-QA-HARD-026',self.b,self.f.root,self.f.snapshot.artifacts[1],b'2+3',self.p,(self.f.snapshot.artifacts[0],),{'synthetic_manual_handoff':True})
  self.ver=ReviewVerifier((KEY,rh.KEY))
 def prepare(self,change=None):
  c=change or self.c
  return prepare_for_controller(c,self.p,self.f.root,self.f.batch,self.f.snapshot,self.f.policy,as_of=rh.NOW,
   review=signed(c,self.p,now=rh.NOW),verifier=self.ver,inventory_reviews=self.f.inv())
 def test_existing_controller_actual_staging(self):
  self.setup_change();p,r=self.prepare();out=self.f.run_proposal(p);self.assertEqual(out['status'],'STAGED_FOR_REVIEW');self.assertTrue(out['worker_executed']);self.assertFalse(out['product_accepted'])
 def test_new_proposal_requires_separate_approval(self):
  self.setup_change();p,r=self.prepare()
  with self.assertRaises(ContractError):self.f.run_proposal(p,proposal_reviews=())
 def test_wrong_fix_fails_native_validator(self):
  self.setup_change();p,r=self.prepare(replace(self.c,payload=b'2+8'));out=self.f.run_proposal(p);self.assertEqual(out['status'],'REJECTED')
 def test_missing_downstream_check_rejected(self):
  self.setup_change();self.p=replace(self.p,required_checks=self.p.required_checks+('new-check',));self.c=replace(self.c,scope_digest=self.p.content_digest,binding=replace(self.c.binding,policy_digest=self.p.content_digest),required_checks=self.p.required_checks)
  self.error('H6_CONTROLLER_CHECK_OMISSION',self.prepare)
 def test_missing_invalidation_rejected(self):
  self.setup_change();self.p=replace(self.p,invalidates=self.p.invalidates+('new-check',));self.c=replace(self.c,scope_digest=self.p.content_digest,binding=replace(self.c.binding,policy_digest=self.p.content_digest),invalidates=self.p.invalidates)
  self.error('H6_CONTROLLER_CHECK_OMISSION',self.prepare)
 def test_changed_original_rejected(self):
  self.setup_change();(self.f.root/'generated/lesson.txt').write_bytes(b'changed')
  with self.assertRaises(ContractError):self.prepare()
 def test_repeated_prepare_no_overwrite(self):
  self.setup_change();p,r=self.prepare()
  with self.assertRaises(FileExistsError):self.prepare()
