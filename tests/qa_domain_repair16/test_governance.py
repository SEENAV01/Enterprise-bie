from domain_helpers import *
import os,subprocess
class GovernanceTests(Base):
 def test_missing_inventory_authority(self):
  c=self.context();self.assertError('DOMAIN_REPAIR_INVENTORY_APPROVAL_REQUIRED',c.generate,inventory_reviews=())
 def test_missing_generation_authority(self):
  c=self.context();self.assertError('DOMAIN_REPAIR_GENERATION_APPROVAL_REQUIRED',c.generate,generation_reviews=())
 def test_wrong_generation_digest(self):
  c=self.context();auth=(c.signed(c.job.job_id,'inference','0'*64,(c.target.artifact_id,)),);self.assertError('DOMAIN_REPAIR_GENERATION_APPROVAL_REQUIRED',c.generate,generation_reviews=auth)
 def test_uncertain_generation_authority(self):
  c=self.context();auth=(c.signed(c.job.job_id,'inference',c.job.content_digest,(c.target.artifact_id,),verdict='UNCERTAIN'),);self.assertError('DOMAIN_REPAIR_GENERATION_APPROVAL_REQUIRED',c.generate,generation_reviews=auth)
 def test_rejection_cannot_be_outvoted(self):
  c=self.context();bad=c.signed(c.job.job_id,'inference',c.job.content_digest,(c.target.artifact_id,),verdict='REJECTED',review_id='negative');self.assertError('DOMAIN_REPAIR_GENERATION_APPROVAL_REQUIRED',c.generate,generation_reviews=c.gen_auth()+(bad,))
 def test_expired_generation_authority(self):
  c=self.context();bad=c.signed(c.job.job_id,'inference',c.job.content_digest,(c.target.artifact_id,),issued_at=c.now-100,expires_at=c.now-1);self.assertError('DOMAIN_REPAIR_GENERATION_APPROVAL_REQUIRED',c.generate,generation_reviews=(bad,))
 def test_revoked_key(self):
  c=self.context();c.verifier=ReviewVerifier((replace(KEY,enabled=False),));self.assertError('DOMAIN_REPAIR_INVENTORY_APPROVAL_REQUIRED',c.generate)
 def test_test_only_key_not_promoted(self):
  c=self.context();c.verifier=ReviewVerifier((replace(KEY,assurance='test_only'),));self.assertError('DOMAIN_REPAIR_INVENTORY_APPROVAL_REQUIRED',c.generate)
 def test_domain_policy_swap(self):
  c=self.context();c.dp=replace(c.dp,policy_id='other');self.assertError('DOMAIN_REPAIR_JOB_BINDING',c.generate)
 def test_limits_swap(self):
  c=self.context();c.limits=Limits(max_added_ms=999);self.assertError('DOMAIN_REPAIR_JOB_BINDING',c.generate)
 def test_target_not_owned(self):
  c=self.context();c.policy=replace(c.policy,routes=(replace(c.policy.routes[0],mutable_paths=('generated/other.json',)),));c.refresh();self.assertError('DOMAIN_REPAIR_TARGET_NOT_OWNED',c.generate)
 def test_nonautomatic_failure(self):
  c=self.context();c.policy=replace(c.policy,rules=tuple(replace(r,automatic=False) for r in c.policy.rules));c.refresh();self.assertError('DOMAIN_REPAIR_NO_AUTHORIZED_FAILURE',c.generate)
 def test_wrong_report_request_not_targeted(self):
  c=self.context();r=json.loads((c.root/c.bound.artifact.path).read_text());r['request_digest']='0'*64;ref=c.write(c.bound.artifact.path,canonical_bytes(r),c.bound.artifact.artifact_id,'report');c.bound=replace(c.bound,artifact=ref,request_digest='0'*64);c.batch=replace(c.batch,reports=(c.bound,));c.refresh();self.assertError('DOMAIN_REPAIR_NO_AUTHORIZED_FAILURE',c.generate)
 def test_prepare_does_not_publish_candidate(self):
  c=self.context();p,r=c.prepare();self.assertEqual((c.root/c.target.path).read_bytes(),c.original_bytes[c.target.path]);self.assertFalse(r['canonical_repository_modified']);self.assertFalse(r['product_accepted'])
 def test_proposal_requires_fresh_approval(self):
  c=self.context();p,r=c.prepare();self.assertError('REPAIR_PROPOSAL_APPROVAL_REQUIRED',c.execute,p,proposal_reviews=c.gen_auth())
 def test_proposal_path_no_overwrite(self):
  c=self.context();c.prepare();self.assertError('DOMAIN_REPAIR_PROPOSAL_EXISTS_OR_UNSAFE',c.prepare)
 def test_symlink_proposal_rejected(self):
  c=self.context();out=self.home/'outside';out.mkdir();(c.root/'proposals').symlink_to(out,target_is_directory=True);self.assertError('DOMAIN_REPAIR_PROPOSAL_SYMLINK',c.prepare)
 def test_source_symlink_rejected(self):
  c=self.context();p=c.root/c.candidate.artifacts[0].path;outside=self.home/'source';p.rename(outside);p.symlink_to(outside);self.assertError('ARTIFACT_OPEN_OR_READ_FAILED',c.generate)
 def test_preserve_invalidation(self):
  c=self.context();g=c.generate();self.assertIn('preserve',g.required_checks);self.assertIn('domain',g.invalidated_checks);self.assertFalse(g.receipt()['previous_candidate_reviews_reusable'])
 def test_deterministic_payload(self):
  c=self.context();a=c.generate();b=c.generate();self.assertEqual(a,b);self.assertEqual(a.content_digest,b.content_digest)
 def test_missing_post_assessments_prevents_stage(self):
  c=self.context();p,r=c.prepare();c.positive_assessments=False;out=c.execute(p);self.assertEqual(out['status'],'REJECTED')
 def test_validator_identity_mismatch(self):
  c=self.context();p,r=c.prepare();self.assertError('REPAIR_VALIDATOR_IDENTITY_MISMATCH',c.execute,p,checks={'domain':forged_check,'preserve':preserve_check})
 def test_end_to_end_source(self):self.end_to_end(4)
 def test_end_to_end_reasoning(self):self.end_to_end(5)
 def test_end_to_end_pedagogy(self):self.end_to_end(6)
 def test_end_to_end_director(self):self.end_to_end(7)
 def end_to_end(self,n):
  c=self.context(n);p,g=c.prepare();r=c.execute(p);self.assertEqual(r['status'],'STAGED_FOR_REVIEW',r);self.assertTrue(r['worker_executed']);self.assertFalse(r['product_accepted']);self.assertEqual([x['status'] for x in r['outcomes']],['PASS','PASS'])
  self.assertEqual(c.original_bytes,{a.path:(c.root/a.path).read_bytes() for a in c.snapshot.artifacts})
 def test_job_unknown_task(self):
  c=self.context();self.assertRaises(ContractError,replace,c.job,task_id='BIE-QA-REPAIR-999')
 def test_protected_target(self):
  c=self.context();self.assertRaises(ContractError,replace,c.job,target=replace(c.target,path='tests/request.json'))
 def test_unknown_json_fields(self):
  c=self.context();obj=asdict(c.bad);obj['exec']='arbitrary code';self.assertRaises(ContractError,read_request,c.task,canonical_bytes(obj))
 def test_duplicate_json_keys(self):
  self.assertRaises(ContractError,read_request,'BIE-QA-REPAIR-004',b'{"x":1,"x":2}')
 def test_noninteger_json(self):self.assertRaises(ContractError,read_request,'BIE-QA-REPAIR-004',b'{"x":NaN}')
 def test_bad_limits(self):
  for change in ({'max_proof_calls':0},{'max_total_logic_visits':True},{'max_added_ms':-1},{'max_generated_bytes':0}):
   with self.subTest(change=change):self.assertRaises(ContractError,Limits,**change)
 def test_cli_read_only(self):
  c=self.context();policy=self.home/'policy.json';policy.write_bytes(canonical_bytes(asdict(c.dp)))
  run=subprocess.run([sys.executable,'-B','-m','bie.qa.domain_repair_v2',c.task,str(c.root/c.target.path),str(policy),'--root',str(c.root)],cwd=W,env={**os.environ,'PYTHONPATH':str(W),'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=10)
  self.assertEqual(run.returncode,3,run.stderr);out=json.loads(run.stdout);self.assertEqual(out['status'],'UNAUTHORIZED_PREVIEW_ONLY');self.assertFalse(out['publication_performed']);self.assertFalse((c.root/'proposals').exists())
 def test_topological_cycle(self):self.assertError('DOMAIN_REPAIR_CYCLE',stable_topology,('a','b'),(('a','b'),('b','a')))
 def test_topological_stability(self):self.assertEqual(stable_topology(('z','a','b'),()),('z','a','b'))
 def test_topological_no_hidden_node(self):self.assertError('DOMAIN_REPAIR_MISSING_NODE',stable_topology,('a','b'),(('a','c'),))
 def test_topological_duplicate(self):self.assertError('DOMAIN_REPAIR_DUPLICATE_NODE',stable_topology,('a','a'),())

 def test_wrong_report_policy_not_targeted(self):
  c=self.context();r=json.loads((c.root/c.bound.artifact.path).read_text());r['policy_digest']='0'*64;ref=c.write(c.bound.artifact.path,canonical_bytes(r),c.bound.artifact.artifact_id,'report');c.bound=replace(c.bound,artifact=ref,evaluator_policy_digest='0'*64);c.batch=replace(c.batch,reports=(c.bound,));c.refresh();self.assertError('DOMAIN_REPAIR_NO_AUTHORIZED_FAILURE',c.generate)

 def test_topology_exhaustive_small_routes(self):
  import itertools
  for route in itertools.permutations(('a','b','c','d')):
   with self.subTest(route=route):
    out=stable_topology(route,(('a','b'),('a','c'),('b','d'),('c','d')));self.assertEqual(set(out),set(route));self.assertTrue(out.index('a')<out.index('b')<out.index('d'));self.assertTrue(out.index('a')<out.index('c')<out.index('d'))
 def test_generated_fix_not_self_signed(self):
  c=self.context();g=c.generate();self.assertNotIn('signature',g.receipt());self.assertFalse(g.receipt()['previous_candidate_reviews_reusable'])
 def test_downstream_scope_matches_existing_controller(self):
  from bie.qa.repair_v2.planner import check_closure
  c=self.context();g=c.generate();self.assertEqual((g.required_checks,g.invalidated_checks),check_closure(c.policy,TASK_OWNERS[c.task]))
