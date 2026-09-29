from dataclasses import asdict,replace
from pathlib import Path
from io import BytesIO
import copy,hashlib,json,os,subprocess,sys,unittest
from PIL import Image
from bie.qa.release_v2.contracts import ContractError,canonical_bytes,digest,ReleaseCandidate
from bie.qa.regression_v2.models import *
from bie.qa.regression_v2.diffs import artifact_diff,semantic_diff,visual_diff,game_diff,semantic_snapshot,game_snapshot
from bie.qa.regression_v2.evaluator import inspect_execution
from bie.qa.regression_v2.bridge import prepare_release_evidence
from bie.qa.repair_v2.codec import decode
from bie.qa.source_v2.codec import loads
from regression17_support import *

class Base(unittest.TestCase):
    def setUp(self):self.f=Fixture();self.addCleanup(self.f.close)
    def assertCode(self,code,index=None):self.assertIn(code,codes(self.f.evaluate(),index))

class Core(Base):
    def test_healthy_bounded_authenticated_checks(self):
        r=self.f.evaluate();self.assertEqual(r.status,'CHECKS_PASSED');self.assertFalse(r.to_dict()['product_accepted']);self.assertEqual(len(r.reports),5)
    def test_default_no_authority_requires_review(self):self.assertEqual(self.f.evaluate(reviews=(),verifier=ReviewVerifier()).status,'REVIEW_REQUIRED')
    def test_deterministic_reports(self):self.assertEqual(canonical_bytes(self.f.evaluate().to_dict()),canonical_bytes(self.f.evaluate().to_dict()))
    def test_input_bytes_unchanged_after_evaluation(self):
        before={str(p):p.read_bytes() for p in self.f.root.rglob('*') if p.is_file()};self.f.evaluate();self.assertEqual(before,{str(p):p.read_bytes() for p in self.f.root.rglob('*') if p.is_file()})
    def test_changed_bytes_not_metadata(self):
        (self.f.right/'generated/value.json').write_text('{"answer":5}');self.assertEqual(self.f.evaluate().status,'BLOCKED')
    def test_missing_actual_file(self):
        (self.f.right/'generated/frame.png').unlink();self.assertEqual(self.f.evaluate().status,'BLOCKED')
    def test_extra_file(self):
        (self.f.right/'generated/extra.txt').write_text('extra');self.assertCode('AUDIT_SNAPSHOT_FILE_SET')
    def test_symlink_rejected(self):
        p=self.f.right/'generated/value.json';p.unlink();p.symlink_to(self.f.left/'generated/value.json');self.assertCode('AUDIT_UNSAFE_ENTRY')
    def test_hardlink_rejected(self):
        p=self.f.right/'generated/value.json';p.unlink();os.link(self.f.left/'generated/value.json',p);self.assertCode('AUDIT_UNSAFE_ENTRY')
    def test_protected_fixture_changed(self):
        self.f.set_json('fixture',{'answer':9});self.f.refresh();self.assertCode('REG_FIXTURE_OR_PROTECTED_CHANGED')
    def test_same_root_rejected(self):
        r=evaluate(self.f.request,self.f.left,self.f.left,self.f.evidence,self.f.policy,as_of=NOW);self.assertIn('REG_ROOT_OVERLAP',codes(r))
    def test_evidence_inside_candidate_rejected(self):
        r=evaluate(self.f.request,self.f.left,self.f.right,self.f.right,self.f.policy,as_of=NOW);self.assertIn('REG_EVIDENCE_ROOT_OVERLAP',codes(r))
    def test_receipt_tamper_is_not_execution(self):
        (self.f.evidence/'execution.json').write_text('{}');self.assertEqual(self.f.evaluate().reports[0].status,'BLOCKED')
    def test_wire_round_trip(self):
        for v in (self.f.request,self.f.policy):self.assertEqual(decode(loads(canonical_bytes(asdict(v))),type(v)),v)
    def test_unexpected_wire_fields_rejected(self):
        raw=asdict(self.f.policy);raw['shell']='echo PASS'
        with self.assertRaises(ContractError):decode(loads(canonical_bytes(raw)),RegressionPolicy)
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ContractError):loads(b'{"x":1,"x":2}')
    def test_float_json_rejected(self):
        with self.assertRaises(ContractError):loads(b'{"x":1.1}')
    def test_unsigned_bridge_never_passes(self):
        c=ReleaseCandidate('2.0.0','candidate',self.f.candidate.run_id,self.f.candidate.revision,self.f.candidate.artifacts)
        p=prepare_release_evidence(self.f.request,self.f.left,self.f.right,self.f.evidence,self.f.policy,c,as_of=NOW,reviews=self.f.reviews,verifier=VERIFIER)
        self.assertEqual(p.envelope.status,'NOT_RUN');self.assertEqual(p.envelope.signature,'')
    def test_bridge_failed_check_is_fail(self):
        self.f.set_json('calc',{'answer':5});self.f.refresh(permit=False)
        c=ReleaseCandidate('2.0.0','candidate',self.f.candidate.run_id,self.f.candidate.revision,self.f.candidate.artifacts)
        p=prepare_release_evidence(self.f.request,self.f.left,self.f.right,self.f.evidence,self.f.policy,c,as_of=NOW,reviews=self.f.reviews,verifier=VERIFIER)
        self.assertEqual(p.envelope.status,'FAIL')
    def test_bridge_wrong_candidate_rejected(self):
        c=ReleaseCandidate('2.0.0','candidate',self.f.baseline.run_id,self.f.baseline.revision,self.f.baseline.artifacts)
        with self.assertRaises(ContractError):prepare_release_evidence(self.f.request,self.f.left,self.f.right,self.f.evidence,self.f.policy,c,as_of=NOW)
    def test_cli_read_only_unsigned(self):
        self._cli_inputs();p=self._cli('result.json');self.assertEqual(p.returncode,3,p.stderr);self.assertIn('REVIEW_REQUIRED',p.stdout)
    def test_cli_existing_output_not_overwritten(self):
        self._cli_inputs();out=self.f.root/'result.json';out.write_bytes(b'preserve');p=self._cli('result.json');self.assertEqual(p.returncode,4);self.assertEqual(out.read_bytes(),b'preserve')
    def test_cli_cannot_write_candidate_tree(self):
        self._cli_inputs();p=self._cli('candidate/new.json');self.assertEqual(p.returncode,4);self.assertFalse((self.f.right/'new.json').exists())
    def _cli_inputs(self):
        for n,v in [('request',self.f.request),('policy',self.f.policy)]: (self.f.root/(n+'.json')).write_bytes(canonical_bytes(asdict(v)))
    def _cli(self,out):
        return subprocess.run([sys.executable,'-B','-m','bie.qa.regression_v2','--request',str(self.f.root/'request.json'),'--policy',str(self.f.root/'policy.json'),'--baseline-root',str(self.f.left),'--candidate-root',str(self.f.right),'--evidence-root',str(self.f.evidence),'--output',str(self.f.root/out),'--as-of',str(NOW)],capture_output=True,text=True,timeout=15)

class Artifacts(Base):
    def test_explicit_change_allowed_at_artifact_level(self):
        self.f.set_json('calc',{'answer':5});self.f.refresh();self.assertEqual(self.f.evaluate().reports[1].status,'CHECKS_PASSED')
    def test_unapproved_change_blocked(self):
        self.f.set_json('calc',{'answer':5});self.f.refresh(permit=False);self.assertCode('REG_UNAPPROVED_ARTIFACT_CHANGE',1)
    def test_added_artifact_is_reported(self):
        self.f.b['new']=('generated/new.json',b'{"v":1}','support');self.f.refresh();r=self.f.evaluate();self.assertEqual(r.reports[1].status,'CHECKS_PASSED');self.assertEqual(json.loads(r.diff_json)['artifacts'][0]['kind'],'ADDED')
    def test_removed_unprotected_artifact_is_reported(self):
        del self.f.b['calc'];self.f.refresh();self.assertEqual(self.f.evaluate().reports[1].status,'CHECKS_PASSED')
    def test_path_change_not_hidden_by_identical_bytes(self):
        _,data,role=self.f.b['calc'];self.f.b['calc']=('generated/renamed.json',data,role);self.f.refresh(permit=False);self.assertCode('REG_UNAPPROVED_ARTIFACT_CHANGE',1)
    def test_role_change_not_hidden_by_hash(self):
        path,data,_=self.f.b['calc'];self.f.b['calc']=(path,data,'game');self.f.refresh(permit=False);self.assertCode('REG_UNAPPROVED_ARTIFACT_CHANGE',1)
    def test_old_permit_does_not_approve_new_bytes(self):
        self.f.set_json('calc',{'answer':5});self.f.refresh();per=self.f.policy.change_permits;self.f.set_json('calc',{'answer':6});self.f.refresh();self.f.policy=replace(self.f.policy,change_permits=per);self.assertCode('REG_UNAPPROVED_ARTIFACT_CHANGE',1)
    def test_unused_permit_rejected(self):
        self.f.policy=replace(self.f.policy,change_permits=(ChangePermit('calc','a'*64,'b'*64,'test'),));self.assertCode('REG_UNUSED_CHANGE_PERMIT',1)
    def test_renaming_id_is_delete_and_add(self):
        self.f.b['calc2']=self.f.b.pop('calc');self.f.refresh();d,issues=artifact_diff(self.f.baseline,self.f.candidate,self.f.policy);self.assertEqual({x['kind'] for x in d},{'ADDED','REMOVED'});self.assertFalse(issues)

class Semantic(Base):
    def change(self,fn):
        o=semantic();fn(o);self.f.set_json('sem',o);self.f.refresh()
    def test_removed_required_claim(self):self.change(lambda o:o['claims'].clear());self.assertCode('REG_REQUIRED_CLAIM_LOST',2)
    def test_removed_required_concept(self):
        self.change(lambda o:(o['concept_ids'].remove('addition'),o['claims'].clear(),o['relations'].clear()));self.assertCode('REG_REQUIRED_CONCEPT_LOST',2)
    def test_lost_condition_blocks_even_with_authority(self):self.change(lambda o:o['claims'][0]['conditions'].clear());self.assertCode('REG_SEM_CONDITION_LOST',2)
    def test_lost_source_blocks(self):
        self.change(lambda o:o['claims'][0].update(source_refs=['other-source']));self.assertCode('REG_SEM_SOURCE_LOST',2)
    def test_changed_expression_needs_review(self):self.change(lambda o:o['claims'][0].update(expression='2+2=5'));self.assertCode('REG_SEM_MEANING_REVIEW',2)
    def test_paraphrase_is_not_automatic_equivalence(self):self.change(lambda o:o['claims'][0].update(text='Four is two plus two.'));self.assertEqual(self.f.evaluate().reports[2].status,'REVIEW_REQUIRED')
    def test_confidence_increase_needs_review(self):self.change(lambda o:o['claims'][0].update(confidence_ppm=1000000));self.assertCode('REG_SEM_MEANING_REVIEW',2)
    def test_contradiction_blocks(self):self.change(lambda o:o['claims'][0].update(status='CONTRADICTED'));self.assertCode('REG_SEM_CONTRADICTED',2)
    def test_uncertainty_not_a_pass(self):self.change(lambda o:o['claims'][0].update(status='UNCERTAIN'));self.assertCode('REG_SEM_UNCERTAIN',2)
    def test_relation_loss(self):self.change(lambda o:o['relations'].clear());self.assertCode('REG_SEM_RELATION_LOST',2)
    def test_duplicate_claim_ids(self):self.change(lambda o:o['claims'].append(copy.deepcopy(o['claims'][0])));self.assertCode('REG_SEM_CLAIM_INVENTORY',2)
    def test_missing_source_refs(self):self.change(lambda o:o['claims'][0].update(source_refs=[]));self.assertCode('REG_SEM_UNGROUNDED',2)
    def test_unknown_concept_reference(self):self.change(lambda o:o['claims'][0].update(concept_id='unknown'));self.assertCode('REG_SEM_CLAIM_INVENTORY',2)
    def test_duplicate_relation(self):self.change(lambda o:o['relations'].append(copy.deepcopy(o['relations'][0])));self.assertCode('REG_SEM_DUPLICATE_RELATION',2)
    def test_reordered_claims_not_semantic_change(self):
        o=semantic();o['claims'].append({**o['claims'][0],'claim_id':'claim2'});a=canonical_bytes(o);o['claims'].reverse();d,issues=semantic_diff(a,canonical_bytes(o),self.f.policy.semantic[0]);self.assertFalse(d['claim_changes']);self.assertFalse(issues)
    def test_whitespace_not_silently_normalized(self):self.change(lambda o:o['claims'][0].update(text='Two  plus two equals four.'));self.assertCode('REG_SEM_MEANING_REVIEW',2)
    def test_extra_semantic_fields_fail(self):self.change(lambda o:o.update(trust_me=True));self.assertCode('REG_SEM_SCHEMA',2)

class Visual(Base):
    def rule(self,**kw):return replace(self.f.policy.visual[0],**kw)
    def diff(self,data,rule=None):return visual_diff(image(),data,rule or self.rule())
    def test_identical_pixels_no_diff(self):d,i=self.diff(image());self.assertEqual(d['changed_pixels'],0);self.assertFalse(i)
    def test_single_pixel_detected(self):d,i=self.diff(image([((2,3),(0,0,0))]));self.assertEqual(d['changed_pixels'],1);self.assertEqual(d['bbox'],[2,3,3,4]);self.assertEqual(i[0][0],'REG_VISUAL_DIFFERENCE')
    def test_maximum_not_averaged(self):d,_=self.diff(image([((2,3),(0,0,0))]));self.assertEqual(d['max_channel_delta'],220)
    def test_channel_tolerance_exact_boundary(self):d,i=self.diff(image([((2,3),(219,220,220))]),self.rule(channel_tolerance=1));self.assertEqual(d['changed_pixels'],0);self.assertFalse(i)
    def test_fraction_floor_does_not_hide_change(self):
        d,i=self.diff(image([((2,3),(0,0,0))]),self.rule(changed_pixel_limit_ppm=5208));self.assertTrue(i) # 1/192 > 5208/1e6
    def test_explicit_fraction_limit(self):d,i=self.diff(image([((2,3),(0,0,0))]),self.rule(changed_pixel_limit_ppm=5209));self.assertFalse(i)
    def test_critical_region_overrides_global_tolerance(self):
        d,i=self.diff(image([((2,3),(219,220,220))]),self.rule(channel_tolerance=4,changed_pixel_limit_ppm=100000,critical_regions=(Box(2,3,1,1),)));self.assertIn('REG_CRITICAL_VISUAL_DIFFERENCE',{x[0] for x in i})
    def test_allowed_mask_is_measured(self):d,i=self.diff(image([((2,3),(0,0,0))]),self.rule(masks=(Box(2,3,1,1),)));self.assertEqual(d['masked_pixels'],1);self.assertFalse(i)
    def test_pixel_outside_mask_still_counted(self):d,i=self.diff(image([((3,3),(0,0,0))]),self.rule(masks=(Box(2,3,1,1),)));self.assertTrue(i)
    def test_whole_image_mask_forbidden(self):
        with self.assertRaises(ContractError):self.rule(masks=(Box(0,0,16,12),))
    def test_mask_cannot_cover_critical_region(self):
        with self.assertRaises(ContractError):self.rule(masks=(Box(0,0,1,1),),critical_regions=(Box(0,0,2,2),))
    def test_dimension_change_not_resized(self):
        with self.assertRaises(ContractError):self.diff(image(size=(12,16)))
    def test_non_png_rejected(self):
        b=BytesIO();Image.new('RGB',(16,12)).save(b,format='JPEG')
        with self.assertRaises(ContractError):self.diff(b.getvalue())
    def test_corrupt_png_rejected(self):
        with self.assertRaises(ContractError):self.diff(b'not-an-image')
    def test_alpha_change_detected(self):
        a=image(rgba=True);b=image([((2,3),(220,220,220,0))],rgba=True);d,i=visual_diff(a,b,self.rule());self.assertEqual(d['max_channel_delta'],255);self.assertTrue(i)
    def test_hidden_rgb_not_dropped(self):
        a=image([((2,3),(220,220,220,0))],rgba=True);b=image([((2,3),(0,0,0,0))],rgba=True);d,i=visual_diff(a,b,self.rule());self.assertTrue(i)
    def test_color_profile_requires_review(self):
        b=BytesIO();Image.new('RGB',(16,12),(220,220,220)).save(b,format='PNG',icc_profile=b'unsupported-test-profile');d,i=self.diff(b.getvalue());self.assertIn('REG_COLOR_PROFILE_REVIEW',{x[0] for x in i})
    def test_unchanged_different_encoding_is_pixel_equal(self):
        b=BytesIO();Image.new('RGB',(16,12),(220,220,220)).save(b,format='PNG',compress_level=0);d,i=self.diff(b.getvalue());self.assertFalse(i)

class Games(Base):
    def change(self,fn):o=game();fn(o);self.f.set_json('game',o);self.f.refresh()
    def test_score_difference(self):self.change(lambda o:o['runs'][0]['steps'][1].update(score=999));self.assertCode('REG_GAME_STATE_REGRESSION',4)
    def test_feedback_difference(self):self.change(lambda o:o['runs'][0]['steps'][1].update(feedback='Wrong fact.'));self.assertCode('REG_GAME_STATE_REGRESSION',4)
    def test_hidden_state_difference(self):self.change(lambda o:o['runs'][0]['steps'][1]['state'].update(hidden_reward=10));self.assertCode('REG_GAME_STATE_REGRESSION',4)
    def test_boolean_not_number(self):
        a=game();a['runs'][0]['steps'][1]['state']['flag']=1;b=copy.deepcopy(a);b['runs'][0]['steps'][1]['state']['flag']=True
        self.f.set_json('game',a,which='a');self.f.set_json('game',b);self.f.refresh();self.assertCode('REG_GAME_STATE_REGRESSION',4)
    def test_input_change(self):self.change(lambda o:o['runs'][0]['steps'][1]['input'].update(answer=9));self.assertCode('REG_GAME_STATE_REGRESSION',4)
    def test_enabled_action_change(self):self.change(lambda o:o['runs'][0]['steps'][1].update(enabled_actions=[]));self.assertCode('REG_GAME_STATE_REGRESSION',4)
    def test_terminal_change(self):self.change(lambda o:o['runs'][0]['steps'][1].update(terminal=False));self.assertCode('REG_GAME_STATE_REGRESSION',4)
    def test_missing_checkpoint(self):self.change(lambda o:o['runs'][0]['steps'].pop());self.assertCode('REG_GAME_STEP_COVERAGE',4)
    def test_reordered_actions(self):self.change(lambda o:o['runs'][0]['steps'].reverse());self.assertCode('REG_GAME_ACTION_ORDER',4)
    def test_missing_scenario(self):self.change(lambda o:o['runs'].clear());self.assertCode('REG_GAME_SCENARIO_COVERAGE',4)
    def test_duplicate_scenario(self):self.change(lambda o:o['runs'].append(copy.deepcopy(o['runs'][0])));self.assertCode('REG_GAME_SCENARIO_IDENTITY',4)
    def test_seed_mismatch(self):self.change(lambda o:o['runs'][0].update(seed=2));self.assertCode('REG_GAME_SCENARIO_IDENTITY',4)
    def test_reported_is_not_runtime(self):self.change(lambda o:o['runs'][0].update(execution_mode='REPORTED'));self.assertCode('REG_GAME_NATIVE_OBSERVATION_PENDING',4)
    def test_node_reducer_is_not_browser(self):self.change(lambda o:o['runs'][0].update(execution_mode='NODE_REDUCER'));self.assertCode('REG_GAME_NATIVE_OBSERVATION_PENDING',4)
    def test_extra_state_schema_fields_rejected(self):self.change(lambda o:o['runs'][0]['steps'][1].update(ignore=True));self.assertCode('REG_GAME_STEP_SCHEMA',4)

class Authentication(Base):
    def test_test_only_key_not_operational(self):
        v=ReviewVerifier((replace(KEY,assurance='test_only'),));self.assertEqual(self.f.evaluate(verifier=v).status,'REVIEW_REQUIRED')
    def test_revoked_key(self):self.assertEqual(self.f.evaluate(verifier=ReviewVerifier((replace(KEY,enabled=False),))).status,'REVIEW_REQUIRED')
    def test_bad_signature(self):r=(replace(self.f.reviews[0],signature='0'*64),)+self.f.reviews[1:];self.assertEqual(self.f.evaluate(reviews=r).status,'REVIEW_REQUIRED')
    def test_stale_review(self):self.assertEqual(self.f.evaluate(as_of=NOW+101).status,'REVIEW_REQUIRED')
    def test_wrong_request_binding(self):r=(replace(self.f.reviews[0],request_digest='0'*64),)+self.f.reviews[1:];self.assertEqual(self.f.evaluate(reviews=r).status,'REVIEW_REQUIRED')
    def test_mapping_missing_not_hidden_by_execution_review(self):self.assertEqual(self.f.evaluate(reviews=self.f.reviews[:2]).reports[2].status,'REVIEW_REQUIRED')
    def test_execution_missing_not_hidden_by_inventory(self):self.assertEqual(self.f.evaluate(reviews=(self.f.reviews[0],self.f.reviews[2])).reports[0].status,'REVIEW_REQUIRED')
    def test_rejection_cannot_be_outvoted(self):
        r=replace(self.f.reviews[0],review_id='rejection',verdict='REJECTED');r=replace(r,signature=hmac.new(SECRET,r.signing_bytes(),hashlib.sha256).hexdigest());self.assertEqual(self.f.evaluate(reviews=self.f.reviews+(r,)).status,'REVIEW_REQUIRED')
    def test_duplicate_review_id_rejected(self):
        with self.assertRaises(ContractError):self.f.evaluate(reviews=self.f.reviews+(self.f.reviews[0],))
    def test_unexpected_review_rejected(self):
        r=replace(self.f.reviews[0],subject_id='other');self.assertIn('REG_UNEXPECTED_REVIEW',codes(self.f.evaluate(reviews=(r,))))

# Each row is a distinct execution-integrity defect, tested after rehashing and
# re-authorizing the record so the semantic guard, not just byte hashes, is tested.
EXECUTION_CASES={
 'acceptance_claim':(lambda r:r.update(product_accepted=True),'REG_EXECUTION_SCOPE'),
 'full_repo_claim':(lambda r:r.update(full_repository_regression_run=True),'REG_EXECUTION_SCOPE'),
 'empty_environment':(lambda r:r.update(environment={}),'REG_ENVIRONMENT_EMPTY'),
 'environment_tamper':(lambda r:r['environment'].update(unknown=True),'REG_ENVIRONMENT_HASH'),
 'stale_record':(lambda r:r.update(evaluated_at=NOW-4000),'REG_EXECUTION_STALE'),
 'future_record':(lambda r:r.update(evaluated_at=NOW+1),'REG_EXECUTION_STALE'),
 'candidate_hash':(lambda r:r['binding'].update(candidate_digest='0'*64),'REG_EXECUTION_BINDING'),
 'policy_hash':(lambda r:r['binding'].update(policy_digest='0'*64),'REG_EXECUTION_BINDING'),
 'not_executed':(lambda r:r['candidate'].update(worker_executed=False),'REG_PHASE_NOT_EXECUTED'),
 'boolean_exit':(lambda r:r['candidate'].update(process_exit=False),'REG_PHASE_NOT_EXECUTED'),
 'bad_exit':(lambda r:r['candidate'].update(process_exit=1),'REG_PHASE_NOT_EXECUTED'),
 'worker_error':(lambda r:r['candidate'].update(error='TIMEOUT'),'REG_PHASE_ERROR'),
 'clock_reverse':(lambda r:r['candidate'].update(wall_finished_ns=1),'REG_PHASE_CLOCK'),
 'phase_overlap':(lambda r:r['candidate'].update(wall_started_ns=110),'REG_PHASE_ORDER'),
 'reused_execution':(lambda r:r['candidate'].update(execution_id=r['baseline']['execution_id']),'REG_EXECUTION_REUSED'),
 'missing_check':(lambda r:r['candidate']['checks'].clear(),'REG_CHECK_COVERAGE'),
 'missing_case':(lambda r:r['candidate']['checks'][0]['cases'].clear(),'REG_CASE_COVERAGE'),
 'changed_validator':(lambda r:r['candidate']['checks'][0].update(validator_digest='0'*64),'REG_CHECK_IDENTITY'),
 'changed_fixture':(lambda r:r['candidate']['checks'][0].update(fixture_ids=['other']),'REG_CHECK_IDENTITY'),
 'wrong_phase_snapshot':(lambda r:r['candidate'].update(snapshot_digest='0'*64),'REG_PHASE_BINDING'),
 'new_failure':(lambda r:r['candidate']['checks'][0]['cases'][0].update(status='FAIL',diagnostics=['BAD']),'REG_PREVIOUS_PASS_REGRESSED'),
 'baseline_not_run':(lambda r:r['baseline']['checks'][0]['cases'][0].update(status='NOT_RUN',diagnostics=['MISSING']),'REG_BASELINE_CASE_UNVERIFIED'),
 'baseline_error':(lambda r:r['baseline']['checks'][0]['cases'][0].update(status='ERROR',diagnostics=['ERROR']),'REG_BASELINE_CASE_UNVERIFIED'),
 'case_not_run':(lambda r:r['candidate']['checks'][0]['cases'][0].update(status='NOT_RUN',diagnostics=['MISSING']),'REG_CANDIDATE_CASE_FAILED'),
 'extra_receipt_field':(lambda r:r.update(override=True),'REG_EXECUTION_SCHEMA'),
}
class ExecutionRecords(Base):pass
for name,(mutation,expected) in EXECUTION_CASES.items():
    def test(self,fn=mutation,code=expected):
        fn(self.f.record);self.f.rebind();self.assertCode(code,0)
    setattr(ExecutionRecords,'test_'+name,test)

class ActualRunner(Base):
    def test_actual_paired_execution(self):
        r=self.f.actual();self.assertTrue(r['baseline']['worker_executed']);self.assertTrue(r['candidate']['worker_executed']);self.assertEqual(self.f.evaluate().reports[0].status,'CHECKS_PASSED')
    def test_actual_new_failure(self):
        self.f.set_json('calc',{'answer':5});self.f.refresh();self.f.actual();self.assertCode('REG_PREVIOUS_PASS_REGRESSED',0)
    def test_actual_fixed_baseline_is_not_regression(self):
        self.f.set_json('calc',{'answer':5},which='a');self.f.refresh();self.f.actual();self.assertEqual(self.f.evaluate().reports[0].status,'CHECKS_PASSED')
    def test_wrong_validator_not_executed(self):
        with self.assertRaises(ContractError):self.f.actual(exception)
    def test_missing_registry_rejected(self):
        with self.assertRaises(ContractError):collect('compare',self.f.baseline,self.f.candidate,self.f.left,self.f.right,self.f.policy,registry={},as_of=NOW)
    def test_mutation_of_private_copy_detected(self):
        self.f.refresh(callback=mutator);r=self.f.actual(mutator);self.assertEqual(r['candidate']['error'],'REG_VALIDATOR_MUTATED_COPY');self.assertEqual(json.loads((self.f.right/'generated/value.json').read_text())['answer'],4)
    def test_callback_exception_recorded(self):
        self.f.refresh(callback=exception);r=self.f.actual(exception);self.assertEqual(r['candidate']['error'],'REG_VALIDATOR_EXCEPTION')
    def test_omitted_case_recorded(self):
        self.f.refresh(callback=omit_case);r=self.f.actual(omit_case);self.assertEqual(r['candidate']['error'],'REG_CASE_COVERAGE')
    def test_bad_callback_return_recorded(self):
        self.f.refresh(callback=bad_return);r=self.f.actual(bad_return);self.assertEqual(r['candidate']['error'],'REG_VALIDATOR_RETURN_TYPE')
    def test_timeout_is_not_pass(self):
        self.f.refresh(callback=timeout,phase_timeout=1);r=self.f.actual(timeout);self.assertEqual(r['candidate']['error'],'REG_WORKER_TIMEOUT');self.assertEqual(self.f.evaluate().reports[0].status,'BLOCKED')

class StrictContracts(Base):
    def test_boolean_dimensions_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.policy.visual[0],width=True)
    def test_negative_box_rejected(self):
        with self.assertRaises(ContractError):Box(-1,0,1,1)
    def test_region_outside_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.policy.visual[0],masks=(Box(16,0,1,1),))
    def test_pixel_budget_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.policy.visual[0],width=4096,height=4096)
    def test_duplicate_masks_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.policy.visual[0],masks=(Box(0,0,1,1),)*2)
    def test_empty_suite_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.policy,checks=())
    def test_duplicate_check_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.policy,checks=self.f.policy.checks*2)
    def test_unprotected_fixture_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.policy,protected_artifact_ids=('calc',))
    def test_empty_domain_not_passed(self):
        for name in ('semantic','visual','game'):
            with self.subTest(domain=name),self.assertRaises(ContractError):replace(self.f.policy,**{name:()})
    def test_duplicate_case_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.policy.checks[0],case_ids=('x','x'))
    def test_protected_change_permit_forbidden(self):
        with self.assertRaises(ContractError):replace(self.f.policy,change_permits=(ChangePermit('fixture','a'*64,'b'*64,'test'),))
    def test_empty_permit_forbidden(self):
        with self.assertRaises(ContractError):ChangePermit('calc','','','test')
    def test_same_digest_permit_forbidden(self):
        with self.assertRaises(ContractError):ChangePermit('calc','a'*64,'a'*64,'test')
    def test_duplicate_scenarios_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.policy.game[0],scenarios=self.f.policy.game[0].scenarios*2)
    def test_first_action_must_initialize(self):
        with self.assertRaises(ContractError):Scenario('x',1,('click',))
    def test_execution_alias_rejected(self):
        a=replace(self.f.baseline.artifacts[0],role='report')
        with self.assertRaises(ContractError):replace(self.f.request,execution=a)
    def test_unknown_comparison_artifact_rejected(self):
        self.f.policy=replace(self.f.policy,semantic=(SemanticRule('missing',('x',),('c',)),));self.assertCode('REG_COMPARISON_ARTIFACT_MISSING')
    def test_boolean_time_rejected(self):
        with self.assertRaises(ContractError):self.f.evaluate(as_of=True)


class Schemas(Base):
    def test_request_schema_accepts_fixture(self):self._validate('regression_request',self.f.request)
    def test_policy_schema_accepts_fixture(self):self._validate('regression_policy',self.f.policy)
    def test_observation_schema_accepts_fixture(self):self._validate('case_observation',Observation('case','PASS',(),'{"actual":true}'))
    def test_schema_rejects_extra_fields(self):
        import jsonschema
        obj=json.loads(canonical_bytes(asdict(self.f.policy)));obj['bypass']=True
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(obj,self._schema('regression_policy'))
    def test_schema_rejects_boolean_integer(self):
        import jsonschema
        obj=json.loads(canonical_bytes(asdict(self.f.policy)));obj['phase_timeout_seconds']=True
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(obj,self._schema('regression_policy'))
    def _schema(self,name):
        return json.loads((Path(__file__).resolve().parents[2]/'docs/qa_section16/batch017'/(name+'.schema.json')).read_text())
    def _validate(self,name,value):
        import jsonschema
        s=self._schema(name);jsonschema.Draft202012Validator.check_schema(s);jsonschema.validate(json.loads(canonical_bytes(asdict(value))),s)

if __name__=='__main__':unittest.main()
