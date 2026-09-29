from vis_helpers import *


class AuthenticationTests(FixtureCase):
    def test_required_target_inventory(self):
        t=review_targets(self.request,self.policy)
        self.assertIn(('inventory','visual-scope'),t);self.assertIn(('mapping','rel-above'),t)
        self.assertIn(('teaching','scene-main'),t)
    def test_duplicate_reviews_rejected(self):
        rr=signed_reviews(self.request,self.policy)
        with self.assertRaises(ContractError):self.run_check(reviews=rr+(rr[0],))
    def test_duplicate_identity_does_not_vote_twice(self):
        rr=signed_reviews(self.request,self.policy)
        with self.assertRaises(ContractError):self.run_check(reviews=rr+(replace(rr[0],review_id='another'),))
    def test_untrusted_keys_fail_closed(self):self.assertEqual(self.run_check(verifier=ReviewVerifier()).status,'BLOCKED')
    def test_test_only_keys_cannot_approve(self):
        k=key(assurance='test_only');self.assertCode(self.run_check(reviews=signed_reviews(self.request,self.policy,k),verifier=ReviewVerifier((k,))),'layout','VIS_TEST_ONLY_ASSESSMENT','REVIEW_REQUIRED')
    def test_revocation(self):self.assertCode(self.run_check(verifier=ReviewVerifier((key(enabled=False),))),'layout','VIS_REVOKED_REVIEW_KEY')
    def test_replay_after_candidate_change(self):
        r=self.measured(font_mpx=25000)
        self.assertCode(self.run_check(r,reviews=signed_reviews(self.request,self.policy)),'layout','VIS_REVIEW_REQUEST_MISMATCH')
    def test_replay_after_policy_change(self):
        p=self.limit(min_font_mpx=19000)
        self.assertCode(self.run_check(p=p,reviews=signed_reviews(self.request,self.policy)),'layout','VIS_REVIEW_POLICY_MISMATCH')
    def test_independence_quorum_missing(self):
        p=replace(self.policy,minimum_independent_assessors=2)
        self.assertCode(self.run_check(p=p),'layout','VIS_CONTEXT_REVIEW_MISSING','REVIEW_REQUIRED')
    def test_two_independent_reviewers(self):
        p=replace(self.policy,minimum_independent_assessors=2);k=key();k2=key(key_id='second-key',evaluator_id='second-assessor',secret=b'SYNTHETIC_SECOND_INDEPENDENT_VIS_KEY_001',independence_group='second-group')
        result=self.run_check(p=p,reviews=signed_reviews(self.request,p,k)+signed_reviews(self.request,p,k2),verifier=ReviewVerifier((k,k2)))
        self.assertEqual(result.status,'CHECKS_PASSED')
    def test_two_same_group_not_independent(self):
        p=replace(self.policy,minimum_independent_assessors=2);k=key();k2=key(key_id='second-key',evaluator_id='second-assessor',secret=b'SYNTHETIC_SECOND_NOT_INDEPENDENT_KEY_001')
        result=self.run_check(p=p,reviews=signed_reviews(self.request,p,k)+signed_reviews(self.request,p,k2),verifier=ReviewVerifier((k,k2)))
        self.assertEqual(result.status,'REVIEW_REQUIRED')
    def test_rejection_not_outvoted(self):
        k=key();k2=key(key_id='reject-key',evaluator_id='reject-assessor',secret=b'SYNTHETIC_REJECTING_ASSESSOR_KEY_0001',independence_group='reject-group')
        rr=signed_reviews(self.request,self.policy,k2);rej=sign(replace(rr[0],verdict='REJECTED'),k2)
        result=self.run_check(reviews=signed_reviews(self.request,self.policy)+(rej,),verifier=ReviewVerifier((k,k2)))
        self.assertCode(result,'layout','VIS_REVIEW_REJECTED','BLOCKED')
    def test_no_secret_in_report(self):self.assertNotIn(key().secret.decode(),json_text(self.run_check().to_dict()))


def json_text(x):return canonical_bytes(x).decode()
AUTH_CASES={
 'bad_signature':({'signature':'0'*64},False,'VIS_BAD_REVIEW_SIGNATURE'),
 'expired':({'issued_at':NOW-100,'expires_at':NOW},True,'VIS_REVIEW_TIME_INVALID'),
 'future':({'issued_at':NOW+1,'expires_at':NOW+60},True,'VIS_REVIEW_TIME_INVALID'),
 'lifetime':({'issued_at':NOW-4000,'expires_at':NOW+60},True,'VIS_REVIEW_LIFETIME_EXCEEDED'),
 'unknown_subject':({'subject_id':'unexpected'},True,'VIS_UNKNOWN_REVIEW_TARGET'),
 'evidence_mismatch':({'evidence_ids':('different-evidence',)},True,'VIS_REVIEW_EVIDENCE_MISMATCH'),
 'uncertain':({'verdict':'UNCERTAIN'},True,'VIS_REVIEW_UNCERTAIN'),
 'low_confidence':({'confidence_ppm':1},True,'VIS_REVIEW_UNCERTAIN'),
 'different_evaluator':({'evaluator_id':'other'},True,'VIS_UNAUTHORIZED_REVIEWER'),
}
for name,(changes,resign,code) in AUTH_CASES.items():
 def test(self,changes=changes,resign=resign,code=code):
    rr=signed_reviews(self.request,self.policy);a=replace(rr[0],**changes)
    if resign:a=sign(a,key())
    self.assertCode(self.run_check(reviews=(a,)+rr[1:]),'layout',code)
 setattr(AuthenticationTests,'test_review_'+name,test)


class CaptureTests(FixtureCase):
    def test_png_bytes_decoded_and_bound_but_sample_not_movie(self):
        r,c=fake_capture(self.root,self.request,self.policy)
        result=self.run_check(r);self.assertEqual(result.verified_capture_ids,('capture-test',));self.assertEqual(result.status,'REVIEW_REQUIRED')
    def test_actual_png_corruption(self):
        r,c=fake_capture(self.root,self.request,self.policy);(self.root/c.screenshot.path).write_bytes(b'not png')
        self.assertEqual(self.run_check(r).status,'BLOCKED')
    def test_hashed_non_png_rejected(self):
        r,c=fake_capture(self.root,self.request,self.policy,png=b'NOT_PNG_BUT_MATCHING_HASH')
        self.assertCode(self.run_check(r),'layout','VIS_CAPTURE_PNG_INVALID')
    def test_image_dimensions_must_match(self):
        from PIL import Image
        from io import BytesIO
        b=BytesIO();Image.new('RGB',(5,5),'white').save(b,format='PNG')
        r,c=fake_capture(self.root,self.request,self.policy,png=b.getvalue())
        self.assertCode(self.run_check(r),'layout','VIS_CAPTURE_PNG_DIMENSIONS_OR_FORMAT')
    def test_measurement_record_cannot_lie_about_state(self):
        r,c=fake_capture(self.root,self.request,self.policy,changes={'state':{}})
        self.assertCode(self.run_check(r),'layout','VIS_CAPTURE_STATE_MISMATCH')
    def test_unrecognized_capture_not_credit(self):
        r,c=fake_capture(self.root,self.request,self.policy);r=replace(r,states=self.request.states)
        self.assertCode(self.run_check(r),'layout','VIS_UNUSED_CAPTURE')
    def test_capture_missing(self):
        r=replace(self.request,states=(replace(self.request.states[0],capture_id='missing'),))
        self.assertCode(self.run_check(r),'layout','VIS_CAPTURE_REFERENCE')
    def test_unsupported_browser_paint_is_review_not_pass(self):
        r,c=fake_capture(self.root,self.request,self.policy,changes={'unsupported':['gradient']})
        self.assertCode(self.run_check(r),'readability','VIS_CAPTURE_UNSUPPORTED','REVIEW_REQUIRED')
    def test_capture_symlink_rejected(self):
        r,c=fake_capture(self.root,self.request,self.policy);p=self.root/c.screenshot.path;data=p.read_bytes();p.unlink();outside=self.root/'elsewhere.png';outside.write_bytes(data);p.symlink_to(outside)
        self.assertEqual(self.run_check(r).status,'BLOCKED')
    def test_capture_html_changed(self):
        r,c=fake_capture(self.root,self.request,self.policy);(self.root/c.html.path).write_bytes(b'changed');self.assertEqual(self.run_check(r).status,'BLOCKED')
    def test_capture_id_cannot_alias_visual(self):
        r,c=fake_capture(self.root,self.request,self.policy)
        with self.assertRaises(ContractError):replace(r,captures=(replace(c,capture_id='object-1'),))
    def test_artifact_identity_cannot_alias(self):
        r,c=fake_capture(self.root,self.request,self.policy)
        with self.assertRaises(ContractError):replace(r,captures=(replace(c,html=replace(c.html,artifact_id='vis-output-artifact')),))

for name,changes,code in [
 ('wrong_view',{'viewport':[900,450]},'VIS_CAPTURE_VIEW_MISMATCH'),
 ('wrong_html_binding',{'html_sha256':'0'*64},'VIS_CAPTURE_HASH_BINDING'),
 ('wrong_png_binding',{'screenshot_sha256':'0'*64},'VIS_CAPTURE_HASH_BINDING'),
 ('wrong_renderer',{'renderer_id':'other'},'VIS_CAPTURE_RENDERER_MISMATCH'),
 ('wrong_mode',{'mode':'whole-movie'},'VIS_CAPTURE_MODE'),
 ('wrong_schema',{'schema_version':'99'},'VIS_CAPTURE_MODE'),
 ('unsupported_not_list',{'unsupported':True},'VIS_CAPTURE_UNSUPPORTED_FIELDS'),
 ('unexpected_field',{'accepted':True},'VIS_CAPTURE_FIELDS')]:
 def test(self,changes=changes,code=code):
    r,c=fake_capture(self.root,self.request,self.policy,changes=changes);self.assertCode(self.run_check(r),'layout',code)
 setattr(CaptureTests,'test_capture_'+name,test)
