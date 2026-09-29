from media_helpers import *
class GovernanceTests(Base):
 def test_new_task_registry_matches(self):self.assertEqual(tuple(TASK_OWNERS),tuple(f'BIE-QA-REPAIR-{i:03}' for i in range(8,12)))
 def test_missing_inventory_authorization(self):
  c=self.context();self.assertError('MEDIA_REPAIR_INVENTORY_APPROVAL_REQUIRED',c.generate,inventory_reviews=())
 def test_missing_generation_authorization(self):
  c=self.context();self.assertError('MEDIA_REPAIR_GENERATION_APPROVAL_REQUIRED',c.generate,generation_reviews=())
 def test_stale_review(self):
  c=self.context();r=c.signed(c.job.job_id,'inference',c.job.content_digest,(c.target.artifact_id,),issued_at=NOW-4000,expires_at=NOW-1);self.assertError('MEDIA_REPAIR_GENERATION_APPROVAL_REQUIRED',c.generate,generation_reviews=(r,))
 def test_wrong_signature(self):
  c=self.context();self.assertError('MEDIA_REPAIR_GENERATION_APPROVAL_REQUIRED',c.generate,generation_reviews=(replace(c.gen()[0],signature='0'*64),))
 def test_wrong_policy_digest(self):
  c=self.context();c.job=replace(c.job,domain_policy_digest='0'*64);self.assertError('MEDIA_REPAIR_JOB_BINDING',c.generate)
 def test_changed_limits_not_silently_accepted(self):
  c=self.context();self.assertError('MEDIA_REPAIR_JOB_BINDING',c.generate,limits=Limits(max_layout_visits=1))
 def test_target_must_be_in_snapshot(self):
  c=self.context();c.job=replace(c.job,target=replace(c.target,artifact_id='alias'),request=replace(c.target,artifact_id='alias'));self.assertError('MEDIA_REPAIR_TARGET_NOT_IN_SNAPSHOT',c.generate)
 def test_report_binding_not_guessed(self):
  c=self.context();b=loads((c.root/c.bound.artifact.path).read_bytes());b['request_digest']='0'*64;ref=c.write(c.bound.artifact.path,canonical_bytes(b),'failure-report','report');c.bound=replace(c.bound,artifact=ref,request_digest='0'*64);c.batch=replace(c.batch,reports=(c.bound,));c.refresh();self.assertError('MEDIA_REPAIR_NO_AUTHORIZED_FAILURE',c.generate)
 def test_report_policy_binding_not_ignored(self):
  c=self.context();b=loads((c.root/c.bound.artifact.path).read_bytes());b['policy_digest']='0'*64;ref=c.write(c.bound.artifact.path,canonical_bytes(b),'failure-report','report');c.bound=replace(c.bound,artifact=ref,evaluator_policy_digest='0'*64);c.batch=replace(c.batch,reports=(c.bound,));c.refresh();self.assertError('MEDIA_REPAIR_NO_AUTHORIZED_FAILURE',c.generate)
 def test_owner_scope(self):
  c=self.context();c.policy=replace(c.policy,routes=(replace(c.policy.routes[0],mutable_paths=('generated/other.json',)),));c.refresh();self.assertError('MEDIA_REPAIR_TARGET_NOT_OWNED',c.generate)
 def test_unknown_failure_not_automatically_repaired(self):
  c=self.context();c.policy=replace(c.policy,rules=(replace(c.policy.rules[0],code='UNKNOWN'),));c.refresh();self.assertError('MEDIA_REPAIR_NO_AUTHORIZED_FAILURE',c.generate)
 def test_generation_deterministic(self):
  c=self.context();self.assertEqual(c.generate(),c.generate())
 def test_generation_is_not_self_approval(self):
  c=self.context();g=c.generate();r=g.receipt();self.assertFalse(r['previous_candidate_reviews_reusable']);self.assertFalse(r['product_accepted']);self.assertEqual(r['status'],'PROPOSAL_GENERATED_REVIEW_REQUIRED')
 def test_required_checks_carried_forward(self):
  c=self.context();g=c.generate();self.assertEqual(g.required_checks,('media','preserve'));self.assertIn('media',g.invalidated_checks)
 def test_prepare_does_not_overwrite(self):
  c=self.context();p,r=c.prepare();self.assertEqual((c.root/c.target.path).read_bytes(),c.original[c.target.path]);self.assertTrue((c.root/p.replacements[0].artifact.path).is_file())
 def test_duplicate_prepare_rejected(self):
  c=self.context();c.prepare();self.assertError('MEDIA_REPAIR_PROPOSAL_EXISTS_OR_UNSAFE',c.prepare)
 def test_symlink_proposal_directory(self):
  c=self.context();(c.root/'proposals').symlink_to(self.home,target_is_directory=True);self.assertError('MEDIA_REPAIR_PROPOSAL_SYMLINK',c.prepare)
 def test_staging_requires_fresh_proposal_approval(self):
  c=self.context();p,_=c.prepare();self.assertError('REPAIR_PROPOSAL_APPROVAL_REQUIRED',c.execute,p,proposal_reviews=c.gen())
 def test_actual_visual_staging(self):
  c=self.context();p,_=c.prepare();r=c.execute(p);self.assertEqual(r['status'],'STAGED_FOR_REVIEW',r);self.assertTrue(r['worker_executed']);self.assertFalse(r['product_accepted'])
 def test_actual_animation_staging(self):
  c=self.context(9);p,_=c.prepare();r=c.execute(p);self.assertEqual(r['status'],'STAGED_FOR_REVIEW',r)
 def test_fresh_semantic_assessment_not_optional(self):
  c=self.context();p,_=c.prepare();c.positive=False;r=c.execute(p);self.assertEqual(r['status'],'REJECTED');self.assertIn('REPAIR_REVALIDATION_NOT_PASS',r['diagnostics'])
 def test_missing_validator_is_not_pass(self):
  c=self.context();p,_=c.prepare();self.assertError('REPAIR_REQUIRED_CHECK_UNAVAILABLE',c.execute,p,checks={})
 def test_read_request_roundtrip(self):
  for n in (8,9,10,11):
   with self.subTest(task=n):
    c=self.context(n);self.assertEqual(read_request(c.task,canonical_bytes(asdict(c.bad))),c.bad)
 def test_read_policy_roundtrip(self):
  for n in (8,9,10,11):
   with self.subTest(task=n):
    c=self.context(n);self.assertEqual(read_policy(c.task,canonical_bytes(asdict(c.dp))),c.dp)
 def test_wire_unknown_fields_rejected(self):
  c=self.context();d=asdict(c.bad);d['approved']=True;self.assertError('REPAIR_JSON_FIELDS',read_request,c.task,canonical_bytes(d))
 def test_bool_is_not_integer_limit(self):self.assertError('INVALID_INTEGER',Limits,max_layout_visits=True)
 def test_protected_target(self):
  c=self.context(10);self.assertError('REPAIR_PROTECTED_PATH',replace,c.job,target=replace(c.target,path='tests/unit.ts'))
 def test_native_policy_not_redefined_in_candidate(self):
  c=self.context();d=asdict(c.bad);d['policy']=asdict(c.dp);self.assertError('REPAIR_JSON_FIELDS',read_request,c.task,canonical_bytes(d))
 def test_duplicate_permissions(self):
  c=self.context();self.assertError('MEDIA_REPAIR_DUPLICATE_PERMISSION',replace,c.dp,permissions=c.dp.permissions*2)
 def test_unknown_window(self):
  c=self.context(9);self.assertError('MEDIA_REPAIR_WINDOW_SCOPE',replace,c.dp,windows=(TrackWindow('unknown',0,100),))
 def test_typed_preview_required(self):
  c=self.context();self.assertError('MEDIA_REPAIR_INPUT_TYPE',preview,c.task,asdict(c.bad),c.root,c.dp)
 def test_no_change_not_staged(self):
  c=self.context();g=c.generate();new=c.write(c.target.path,g.payload);c.target=new;c.request_ref=new;c.snapshot=replace(c.snapshot,artifacts=tuple(new if a.path==new.path else a for a in c.snapshot.artifacts));c.batch=replace(c.batch,snapshot_digest=c.snapshot.content_digest);c.refresh()
  # The old report cannot authorize a repaired request, even before the no-op guard.
  self.assertError('MEDIA_REPAIR_NO_AUTHORIZED_FAILURE',c.generate)
