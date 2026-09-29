from ani_helpers import *
from bie.qa.animation_v2.codec import load_request,load_policy,load_reviews,request_from_dict
from bie.qa.animation_v2.metrics import violates_timing
import json

class ContractTests(FixtureCase):
    def test_request_roundtrip(self):self.assertEqual(load_request(canonical_bytes(asdict(self.r))),self.r)
    def test_policy_roundtrip(self):self.assertEqual(load_policy(canonical_bytes(asdict(self.p))),self.p)
    def test_review_roundtrip(self):self.assertEqual(load_reviews(canonical_bytes([asdict(x) for x in signed_reviews(self.r,self.p)])),signed_reviews(self.r,self.p))
    def test_extra_field_rejected(self):
        d=asdict(self.r);d['accept']=True
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_missing_field_rejected(self):
        d=asdict(self.r);d.pop('tracks')
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(ContractError):load_request(b'{"schema_version":"1.0.0","schema_version":"1.0.0"}')
    def test_duplicate_track_id(self):
        with self.assertRaises(ContractError):replace(self.r,tracks=self.r.tracks+(self.r.tracks[0],))
    def test_keyframe_reverse_order(self):
        with self.assertRaises(ContractError):replace(self.r.tracks[0],keyframes=tuple(reversed(self.r.tracks[0].keyframes)))
    def test_duplicate_keyframe_time(self):
        with self.assertRaises(ContractError):replace(self.r.tracks[0],keyframes=(Keyframe(0,0),Keyframe(0,1)))
    def test_empty_mode(self):
        with self.assertRaises(ContractError):replace(self.r,modes=())
    def test_invalid_fps(self):
        for args in [(0,1),(30,0),(60,2),(1000,1),(True,1),(1,2)]:
            with self.subTest(args=args):
                with self.assertRaises(ContractError):FrameRate(*args)
    def test_invalid_keyframe_scalars(self):
        for value in (True,0.0,float('inf'),'0',1_000_000_001):
            with self.subTest(value=value):
                with self.assertRaises(ContractError):Keyframe(0,value)
    def test_timing_rule_references(self):
        with self.assertRaises(ContractError):replace(self.p,timing_rules=(TimingRule('r','none','narration','cue','before'),))
    def test_timing_self_reference(self):
        with self.assertRaises(ContractError):TimingRule('r','t','t','track','before')
    def test_disclosure_ref_missing(self):
        with self.assertRaises(ContractError):replace(self.p,tracks=(replace(self.p.tracks[0],disclosure_cue_ids=('none',)),)+self.p.tracks[1:])
    def test_invariant_unit_mismatch(self):
        with self.assertRaises(ContractError):replace(self.p,invariants=(Invariant('i','standard','equal',('move-x','opacity'),0,2000,0),))
    def test_invariant_unknown_mode(self):
        with self.assertRaises(ContractError):replace(self.p,invariants=(Invariant('i','other','equal',('move-x','move-y'),0,2000,0),))
    def test_capture_frame_duplicates(self):
        with self.assertRaises(ContractError):CaptureRequirement('standard',(0,0))
    def test_capture_frame_outside(self):
        with self.assertRaises(ContractError):replace(self.p,captures=(CaptureRequirement('standard',(0,10000)),))
    def test_reduced_mode_cannot_drop_learning_targets(self):
        with self.assertRaises(ContractError):replace(self.p,modes=self.p.modes+(replace(self.p.modes[0],mode_id='reduced',kind='reduced'),))
    def test_unknown_interpolation_not_silently_linear(self):
        with self.assertRaises(ContractError):replace(self.r.tracks[0],interpolation='magic')
    def test_extreme_track_work_bounded(self):
        t=self.r.tracks[0]
        ts=tuple(replace(t,track_id='t'+str(i),keyframes=tuple(Keyframe(j,j) for j in range(128))) for i in range(129))
        with self.assertRaises(ContractError):replace(self.r,tracks=ts)
    def test_invalid_evaluation_types(self):
        with self.assertRaises(ContractError):evaluate({},self.root,self.p,as_of=NOW)
    def test_negative_as_of(self):
        with self.assertRaises(ContractError):evaluate(self.r,self.root,self.p,as_of=-1)
    def test_invalid_limit_types(self):
        for name,value in [('max_reversals',True),('max_speed_mpx_per_second',-1),('max_simultaneous_objects',257)]:
            with self.subTest(name=name):
                with self.assertRaises(ContractError):replace(self.p.limits,**{name:value})
    def test_timing_relation_boundaries(self):
        a=self.r.tracks[0];b=replace(self.r.cues[0],start_ms=2000,end_ms=2500)
        cases=[('before',False),('after',True),('start_sync',True),('end_sync',True),('covers',True),('overlaps',True)]
        for rel,want in cases:
            with self.subTest(rel=rel):self.assertEqual(violates_timing(TimingRule('r','move-x','narration','cue',rel),a,b),want)

class TrustTests(FixtureCase):
    def modified(self,**changes):
        rs=list(signed_reviews(self.r,self.p));rs[0]=sign(replace(rs[0],**changes),key());return tuple(rs)
    def test_bad_signature(self):self.assertCode(self.check(reviews=tuple(replace(r,signature='0'*64) for r in signed_reviews(self.r,self.p))),'ANI_BAD_REVIEW_SIGNATURE')
    def test_wrong_request(self):self.assertCode(self.check(reviews=self.modified(request_digest='a'*64)),'ANI_REVIEW_REQUEST_MISMATCH')
    def test_wrong_policy(self):self.assertCode(self.check(reviews=self.modified(policy_digest='a'*64)),'ANI_REVIEW_POLICY_MISMATCH')
    def test_expired(self):self.assertCode(self.check(reviews=self.modified(expires_at=NOW)),'ANI_REVIEW_TIME_INVALID')
    def test_future(self):self.assertCode(self.check(reviews=self.modified(issued_at=NOW+1,expires_at=NOW+60)),'ANI_REVIEW_TIME_INVALID')
    def test_old_receipt(self):self.assertCode(self.check(reviews=self.modified(issued_at=NOW-4000,expires_at=NOW+60)),'ANI_REVIEW_LIFETIME_EXCEEDED')
    def test_test_only_authority(self):self.assertCode(self.check(verifier=ReviewVerifier((key(assurance='test_only'),))),'ANI_TEST_ONLY_REVIEW')
    def test_revoked_key(self):self.assertCode(self.check(verifier=ReviewVerifier((key(enabled=False),))),'ANI_REVOKED_REVIEW_KEY')
    def test_unknown_key(self):self.assertCode(self.check(verifier=ReviewVerifier()),'ANI_UNKNOWN_REVIEW_KEY')
    def test_wrong_reviewer(self):self.assertCode(self.check(reviews=self.modified(evaluator_id='other')),'ANI_UNAUTHORIZED_REVIEWER')
    def test_wrong_version(self):self.assertCode(self.check(reviews=self.modified(evaluator_version='2')),'ANI_UNAUTHORIZED_REVIEWER')
    def test_evidence_changed(self):self.assertCode(self.check(reviews=self.modified(evidence_ids=('unknown',))),'ANI_REVIEW_EVIDENCE_MISMATCH')
    def test_uncertain_review(self):self.assertCode(self.check(reviews=self.modified(verdict='UNCERTAIN')),'ANI_REVIEW_UNCERTAIN')
    def test_low_confidence(self):self.assertCode(self.check(reviews=self.modified(confidence_ppm=100)),'ANI_REVIEW_UNCERTAIN')
    def test_rejection_blocks(self):self.assertEqual(self.check(reviews=self.modified(verdict='REJECTED')).status,'BLOCKED')
    def test_missing_one_review(self):self.assertCode(self.check(reviews=signed_reviews(self.r,self.p)[1:]),'ANI_CONTEXT_REVIEW_MISSING')
    def test_duplicate_review_id(self):
        rs=signed_reviews(self.r,self.p)
        with self.assertRaises(ContractError):self.check(reviews=rs+(rs[0],))
    def test_duplicate_vote(self):
        rs=signed_reviews(self.r,self.p)
        with self.assertRaises(ContractError):self.check(reviews=rs+(sign(replace(rs[0],review_id='extra'),key()),))
    def test_no_quorum_by_same_group(self):
        p=replace(self.p,minimum_independent_assessors=2);k2=key(key_id='other-key',secret=b'OTHER_SYNTHETIC_ANI_TEST_KEY_1234567',evaluator_id='other-assessor')
        rs=signed_reviews(self.r,p)+signed_reviews(self.r,p,k2)
        self.assertCode(self.check(p=p,reviews=rs,verifier=ReviewVerifier((key(),k2))),'ANI_CONTEXT_REVIEW_MISSING')
    def test_independent_quorum(self):
        p=replace(self.p,minimum_independent_assessors=2);k2=key(key_id='other-key',secret=b'OTHER_SYNTHETIC_ANI_TEST_KEY_1234567',evaluator_id='other-assessor',independence_group='other-group')
        rs=signed_reviews(self.r,p)+signed_reviews(self.r,p,k2)
        self.assertEqual(self.check(p=p,reviews=rs,verifier=ReviewVerifier((key(),k2))).status,'CHECKS_PASSED')
    def test_rejection_cannot_be_outvoted(self):
        k2=key(key_id='other-key',secret=b'OTHER_SYNTHETIC_ANI_TEST_KEY_1234567',evaluator_id='other-assessor',independence_group='other-group')
        rs=signed_reviews(self.r,self.p)+tuple(sign(replace(r,verdict='REJECTED'),k2) for r in signed_reviews(self.r,self.p,k2))
        self.assertCode(self.check(reviews=rs,verifier=ReviewVerifier((key(),k2))),'ANI_REVIEW_REJECTED')
    def test_signature_does_not_override_math(self):
        r=change_track(self.r,keyframes=(Keyframe(0,40000),Keyframe(1,200000)))
        self.assertEqual(self.check(r).status,'BLOCKED')
