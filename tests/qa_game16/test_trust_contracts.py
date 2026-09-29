from game_helpers import *
from bie.qa.game_v2.codec import decode,load_request,load_policy
from bie.qa.game_v2.capture import collect

class TrustTests(FixtureCase):
    def test_bad_signature(self):
        rv=list(signed_reviews(self.r,self.p));rv[0]=replace(rv[0],signature='f'*64);self.assertCode(self.check(reviews=tuple(rv)),'GAME_BAD_REVIEW_SIGNATURE')
    def test_rejected_not_outvoted(self):
        k=key();rv=list(signed_reviews(self.r,self.p));rv[0]=sign(replace(rv[0],verdict='REJECTED'),k);self.assertCode(self.check(reviews=tuple(rv)),'GAME_REVIEW_REJECTED')
    def test_uncertain(self):
        k=key();rv=list(signed_reviews(self.r,self.p));rv[0]=sign(replace(rv[0],verdict='UNCERTAIN'),k);self.assertCode(self.check(reviews=tuple(rv)),'GAME_REVIEW_UNCERTAIN')
    def test_review_evidence_wrong(self):
        k=key();rv=list(signed_reviews(self.r,self.p));rv[0]=sign(replace(rv[0],evidence_ids=('wrong',)),k);self.assertCode(self.check(reviews=tuple(rv)),'GAME_REVIEW_EVIDENCE')
    def test_unknown_target(self):
        k=key();rv=list(signed_reviews(self.r,self.p));rv[0]=sign(replace(rv[0],subject_id='wrong'),k);self.assertCode(self.check(reviews=tuple(rv)),'GAME_UNKNOWN_REVIEW_TARGET')
    def test_test_key_not_operational(self):
        k=key(assurance='test_only');self.assertCode(self.check(reviews=signed_reviews(self.r,self.p,k),verifier=ReviewVerifier((k,))),'GAME_TEST_ONLY_REVIEW')
    def test_revoked_key(self):self.assertCode(self.check(verifier=ReviewVerifier((key(enabled=False),))),'GAME_REVOKED_REVIEW_KEY')
    def test_unknown_key(self):self.assertCode(self.check(verifier=ReviewVerifier()),'GAME_UNKNOWN_REVIEW_KEY')
    def test_duplicate_review(self):
        rv=signed_reviews(self.r,self.p);self.assertRaises(ContractError,self.check,reviews=rv+(rv[0],))
    def test_old_review_binding(self):
        r=replace(self.r,game_id='other');self.assertCode(self.check(r,reviews=signed_reviews(self.r,self.p)),'GAME_REVIEW_REQUEST_MISMATCH')
    def test_policy_review_binding(self):self.assertCode(self.check(p=replace(self.p,policy_id='other'),reviews=signed_reviews(self.r,self.p)),'GAME_REVIEW_POLICY_MISMATCH')
    def test_independent_review_quorum(self):self.assertCode(self.check(p=replace(self.p,minimum_independent_assessors=2)),'GAME_AUTHORIZED_REVIEW_REQUIRED')
    def test_changed_lifetime(self):
        k=key();rv=list(signed_reviews(self.r,self.p));rv[0]=sign(replace(rv[0],expires_at=NOW),k);self.assertCode(self.check(reviews=tuple(rv)),'GAME_REVIEW_TIME_INVALID')
    def test_low_confidence(self):
        k=key();rv=list(signed_reviews(self.r,self.p));rv[0]=sign(replace(rv[0],confidence_ppm=900000),k);self.assertCode(self.check(reviews=tuple(rv)),'GAME_REVIEW_UNCERTAIN')
    def test_source_assessment_absent(self):self.assertEqual(self.check(source_assessments=()).status,'REVIEW_REQUIRED')
    def test_no_reviews_does_not_pass(self):self.assertEqual(self.check(reviews=()).status,'REVIEW_REQUIRED')

class ContractTests(FixtureCase):
    def test_roundtrip_request(self):self.assertEqual(load_request(canonical_bytes(asdict(self.r))),self.r)
    def test_roundtrip_policy(self):self.assertEqual(load_policy(canonical_bytes(asdict(self.p))),self.p)
    def test_json_extra(self):
        d=asdict(self.r);d['trust_keys']={};self.assertRaises(ContractError,load_request,canonical_bytes(d))
    def test_json_duplicate(self):self.assertRaises(ContractError,load_request,b'{"run_id":"a","run_id":"b"}')
    def test_json_nan(self):self.assertRaises(ContractError,load_request,b'{"x":NaN}')
    def test_json_bad_type(self):self.assertRaises(ContractError,decode,True,int)
    def test_json_depth(self):self.assertRaises(ContractError,decode,1,int,49)
    def test_paths(self):
        for x in ('../escape','/absolute','a/../b','a\\b','http://evil','a//b'):
            with self.subTest(path=x):self.assertRaises(ContractError,replace,self.p,entrypoint=x)
    def test_policy_bounds(self):
        for field,val in [('replays',1),('replays',5),('max_action_ms',0),('minimum_review_confidence_ppm',0),('max_receipt_age_seconds',999999)]:
            with self.subTest(field=field,val=val):self.assertRaises(ContractError,replace,self.p,**{field:val})
    def test_boolean_rejected(self):self.assertRaises(ContractError,replace,self.p,replays=True)
    def test_source_context(self):self.assertRaises(ContractError,replace,self.r,candidate_digest='0'*64)
    def test_artifact_alias(self):self.assertRaises(ContractError,replace,self.r,outputs=(replace(self.r.outputs[0],artifact_id=self.r.inputs[0].artifact_id),)+self.r.outputs[1:])
    def test_ambiguous_oracle(self):self.assertRaises(ContractError,replace,self.p,transitions=self.p.transitions+(replace(self.p.transitions[0],transition_id='extra'),))
    def test_undistinguishable_state(self):self.assertRaises(ContractError,replace,self.p,states=self.p.states+(replace(self.p.states[0],state_id='duplicate'),))
    def test_missing_initial(self):self.assertRaises(ContractError,replace,self.p,initial_state='missing')
    def test_missing_state_reference(self):self.assertRaises(ContractError,replace,self.p,transitions=(replace(self.p.transitions[0],after='missing'),)+self.p.transitions[1:])
    def test_unsafe_entry(self):self.assertRaises(ContractError,replace,self.p,required_loaded_paths=('bad/../evil',))
    def test_unsupported_action(self):self.assertRaises(ContractError,Action,'evil','eval','body','alert(1)')
    def test_capture_explicit_optin(self):self.assertRaises(ContractError,collect,self.r.outputs,self.r.build_receipt,self.p,self.root,run_id=self.r.run_id,code_revision=REV,issued_at=NOW)
    def test_empty_selector(self):self.assertRaises(ContractError,Action,'a','click','','')
    def test_unused_argument(self):self.assertRaises(ContractError,Action,'a','click','#button','injected')
    def test_success_needs_terminal(self):self.assertRaises(ContractError,replace,self.p.states[0],successful=True)
    def test_unknown_runtime_schema(self):
        rr=load_runtime((self.root/self.r.runtime_receipt.path).read_bytes());self.assertRaises(ContractError,replace,rr,schema_version='unknown')
    def test_duplicate_runtime_replay(self):
        rr=load_runtime((self.root/self.r.runtime_receipt.path).read_bytes());self.assertRaises(ContractError,replace,rr,traces=rr.traces+(rr.traces[0],))
    def test_strict_runtime_bool(self):
        rr=load_runtime((self.root/self.r.runtime_receipt.path).read_bytes());self.assertRaises(ContractError,replace,rr,sandbox_verified=1)
