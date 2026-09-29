from audio_helpers import *
import os

class TrustTests(FixtureCase):
    def test_missing_reviews(self):self.assertCode(self.check(reviews=()),'AUDIO_REVIEW_MISSING')
    def test_test_only_keys(self):
        k=key(assurance='test_only');self.assertCode(self.check(reviews=signed_reviews(self.r,self.p,k),verifier=ReviewVerifier((k,))),'AUDIO_TEST_ONLY_REVIEW')
    def test_unknown_key(self):self.assertEqual(self.check(verifier=ReviewVerifier()).status,'BLOCKED')
    def test_revoked_key(self):self.assertEqual(self.check(verifier=ReviewVerifier((key(enabled=False),))).status,'BLOCKED')
    def test_wrong_signature(self):
        rs=signed_reviews(self.r,self.p);rs=(replace(rs[0],signature='0'*64),)+rs[1:];self.assertCode(self.check(reviews=rs),'AUDIO_BAD_REVIEW_SIGNATURE')
    def test_stale_request(self):
        r=replace(self.r,lesson_id='different');self.assertCode(self.check(r,reviews=signed_reviews(self.r,self.p)),'AUDIO_REVIEW_REQUEST_MISMATCH')
    def test_stale_policy(self):self.assertCode(self.check(p=replace(self.p,policy_id='changed'),reviews=signed_reviews(self.r,self.p)),'AUDIO_REVIEW_POLICY_MISMATCH')
    def test_expired_review(self):
        rs=signed_reviews(self.r,self.p);rs=(sign(replace(rs[0],issued_at=NOW-100,expires_at=NOW),key()),)+rs[1:];self.assertEqual(self.check(reviews=rs).status,'BLOCKED')
    def test_rejection_not_outvoted(self):
        rs=signed_reviews(self.r,self.p);rs=(sign(replace(rs[0],verdict='REJECTED'),key()),)+rs[1:];self.assertCode(self.check(reviews=rs),'AUDIO_REVIEW_REJECTED')
    def test_uncertain_review(self):
        rs=signed_reviews(self.r,self.p);rs=(sign(replace(rs[0],verdict='UNCERTAIN'),key()),)+rs[1:];self.assertEqual(self.check(reviews=rs).status,'REVIEW_REQUIRED')
    def test_low_confidence_review(self):
        rs=signed_reviews(self.r,self.p);rs=(sign(replace(rs[0],confidence_ppm=800000),key()),)+rs[1:];self.assertEqual(self.check(reviews=rs).status,'REVIEW_REQUIRED')
    def test_exact_evidence_set(self):
        rs=signed_reviews(self.r,self.p);rs=(sign(replace(rs[0],evidence_ids=('unrelated',)),key()),)+rs[1:];self.assertCode(self.check(reviews=rs),'AUDIO_REVIEW_EVIDENCE_MISMATCH')
    def test_multiple_independent_reviewers_required(self):self.assertEqual(self.check(p=replace(self.p,minimum_independent_assessors=2)).status,'REVIEW_REQUIRED')
    def test_duplicate_review_identity(self):
        rs=signed_reviews(self.r,self.p)
        with self.assertRaises(ContractError):self.check(reviews=rs+(rs[0],))
    def test_duplicate_vote(self):
        rs=signed_reviews(self.r,self.p)
        with self.assertRaises(ContractError):self.check(reviews=rs+(replace(rs[0],review_id='again'),))
    def test_unknown_review_target(self):
        rs=signed_reviews(self.r,self.p);rs=(sign(replace(rs[0],subject_id='unknown'),key()),)+rs[1:];self.assertCode(self.check(reviews=rs),'AUDIO_UNKNOWN_REVIEW_TARGET')
    def test_symlink_rejected(self):
        f=self.root/self.r.clips[0].wav.path;b=f.read_bytes();g=self.root/'real.wav';g.write_bytes(b);f.unlink();f.symlink_to(g);self.assertEqual(self.check().status,'BLOCKED')
    def test_hardlink_rejected(self):
        f=self.root/self.r.clips[0].wav.path;os.link(f,self.root/'link.wav');self.assertEqual(self.check().status,'BLOCKED')
    def test_missing_file(self):(self.root/self.r.clips[0].timing.path).unlink();self.assertEqual(self.check().status,'BLOCKED')
    def test_path_traversal(self):
        with self.assertRaises(ContractError):replace(self.r.clips[0].wav,path='../secret')
