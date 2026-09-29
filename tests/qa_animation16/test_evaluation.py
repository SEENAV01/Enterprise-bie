from ani_helpers import *
from bie.qa.animation_v2.evaluator import AREAS

class EvaluationTests(FixtureCase):
    def test_healthy_bounded_checks(self):self.assertEqual(self.check().status,'CHECKS_PASSED')
    def test_unsigned_requires_review(self):
        result=evaluate(self.r,self.root,self.p,as_of=NOW);self.assertEqual(result.status,'REVIEW_REQUIRED')
    def test_no_product_acceptance(self):self.assertFalse(self.check().to_dict()['product_accepted'])
    def test_report_recomputation(self):self.assertEqual(verify_reports(self.check(),self.r,self.root,self.p,as_of=NOW,**options(self.r,self.p)),self.check())
    def test_edited_report_rejected(self):
        result=self.check();edited=replace(result,motion=replace(result.motion,measurements=()))
        with self.assertRaises(ContractError):verify_reports(edited,self.r,self.root,self.p,as_of=NOW,**options(self.r,self.p))
    def test_stale_report_rejected(self):
        r=change_track(self.r,keyframes=(Keyframe(0,40000),Keyframe(2100,200000)))
        with self.assertRaises(ContractError):verify_reports(self.check(),r,self.root,self.p,as_of=NOW,**options(r,self.p))
    def test_task_id_mapping(self):self.assertEqual(tuple(getattr(self.check(),k).task_id for k in AREAS),('BIE-QA-ANI-001','BIE-QA-ANI-002','BIE-QA-ANI-003'))
    def test_wrong_lesson(self):self.assertCode(self.check(replace(self.r,lesson_id='other')),'ANI_LESSON_CONTEXT')
    def test_wrong_fps(self):self.assertCode(self.check(replace(self.r,modes=(replace(self.r.modes[0],fps=FrameRate(60)),))),'ANI_MODE_SCOPE')
    def test_changed_duration(self):self.assertCode(self.check(replace(self.r,modes=(replace(self.r.modes[0],duration_ms=4000),))),'ANI_MODE_SCOPE')
    def test_missing_track(self):self.assertCode(self.check(replace(self.r,tracks=self.r.tracks[1:])),'ANI_TRACK_INVENTORY')
    def test_added_track(self):self.assertCode(self.check(replace(self.r,tracks=self.r.tracks+(replace(self.r.tracks[0],track_id='hidden-extra'),))),'ANI_TRACK_INVENTORY')
    def test_relabelled_purpose(self):self.assertCode(self.check(change_track(self.r,purpose='decoration')),'ANI_TRACK_MEANING_CHANGED')
    def test_relabelled_semantic_id(self):self.assertCode(self.check(change_track(self.r,semantic_id='other')),'ANI_TRACK_MEANING_CHANGED')
    def test_hidden_object(self):self.assertCode(self.check(replace(self.r,objects=(replace(self.r.objects[0],role='decoration'),))),'ANI_OBJECT_SCOPE')
    def test_object_lifetime(self):self.assertCode(self.check(change_track(self.r,keyframes=(Keyframe(0,40000),Keyframe(4000,200000)))),'ANI_TRACK_OUTSIDE_LIFETIME')
    def test_cue_moved_to_fit_bad_animation(self):self.assertCode(self.check(replace(self.r,cues=(replace(self.r.cues[0],start_ms=100),))),'ANI_CUE_SCOPE')
    def test_bad_start_sync(self):self.assertCode(self.check(change_track(self.r,keyframes=(Keyframe(51,40000),Keyframe(2000,200000)))),'ANI_TEMPORAL_MISALIGNMENT')
    def test_sync_tolerance_boundary(self):
        result=self.check(change_track(self.r,keyframes=(Keyframe(50,40000),Keyframe(2000,200000))))
        self.assertNotIn('ANI_TEMPORAL_MISALIGNMENT',codes(result))
    def test_conflicting_property_writers(self):
        r=replace(self.r,tracks=self.r.tracks+(replace(self.r.tracks[0],track_id='second-x'),))
        p=replace(self.p,tracks=self.p.tracks+(replace(self.p.tracks[0],track_id='second-x'),))
        self.assertCode(self.check(r,p),'ANI_CONFLICTING_PROPERTY_WRITERS')
    def test_different_properties_can_overlap(self):self.assertNotIn('ANI_CONFLICTING_PROPERTY_WRITERS',codes(self.check()))
    def test_monotone_endpoints_do_not_hide_reversal(self):
        r=change_track(self.r,keyframes=(Keyframe(0,40000),Keyframe(500,150000),Keyframe(1000,50000),Keyframe(2000,200000)))
        self.assertCode(self.check(r),'ANI_TREND_CONTRADICTION')
    def test_wrong_endpoint(self):self.assertCode(self.check(change_track(self.r,keyframes=(Keyframe(0,40000),Keyframe(2000,210000)))),'ANI_ENDPOINT_MEANING')
    def test_value_outside_range(self):self.assertCode(self.check(change_track(self.r,keyframes=(Keyframe(0,-1),Keyframe(2000,200000)))),'ANI_VALUE_RANGE')
    def test_opacity_not_over_one(self):self.assertCode(self.check(change_track(self.r,'opacity',keyframes=(Keyframe(0,1000001),Keyframe(2000,1000000)))),'ANI_PROPERTY_DOMAIN')
    def test_cubic_bezier_review_not_pass(self):self.assertCode(self.check(change_track(self.r,interpolation='cubic_bezier')),'ANI_UNSUPPORTED_INTERPOLATION')
    def test_external_curve_review(self):self.assertEqual(self.check(change_track(self.r,interpolation='external')).status,'REVIEW_REQUIRED')
    def test_unmatched_source_claim(self):
        p=replace(self.p,objects=(replace(self.p.objects[0],claim_ids=('unknown',)),))
        self.assertCode(self.check(p=p),'ANI_SOURCE_CLAIM_COVERAGE')
    def test_high_speed_blocked(self):self.assertCode(self.check(change_track(self.r,keyframes=(Keyframe(0,40000),Keyframe(1,200000)))),'ANI_SPEED_LIMIT')
    def test_zero_net_movement_not_zero_motion(self):
        r=change_track(self.r,keyframes=(Keyframe(0,40000),Keyframe(1,500000),Keyframe(2000,40000)))
        self.assertCode(self.check(r),'ANI_SPEED_LIMIT')
    def test_vector_speed_checked(self):
        r=change_track(self.r,keyframes=(Keyframe(0,0),Keyframe(1000,500000)))
        r=change_track(r,'move-y',keyframes=(Keyframe(0,0),Keyframe(1000,500000)))
        self.assertCode(self.check(r),'ANI_SPEED_LIMIT')
    def test_peak_budget_not_average(self):
        r=change_track(self.r,keyframes=(Keyframe(0,40000),Keyframe(1,500000),Keyframe(2000,500000)))
        self.assertCode(self.check(r),'ANI_PEAK_MOTION_BUDGET')
    def test_small_step_allowed(self):self.assertNotIn('ANI_STEP_JUMP_LIMIT',codes(self.check(change_track(self.r,interpolation='step_end'))))
    def test_large_step_rejected(self):
        r=change_track(self.r,interpolation='step_end',keyframes=(Keyframe(0,0),Keyframe(2000,640000)))
        self.assertCode(self.check(r),'ANI_STEP_JUMP_LIMIT')
    def test_jump_aggregation(self):
        r=change_track(self.r,interpolation='step_end')
        r=change_track(r,'move-y',interpolation='step_end',keyframes=(Keyframe(0,100000),Keyframe(2000,260000)))
        self.assertCode(self.check(r),'ANI_AGGREGATE_STEP_JUMP')
    def test_reversal_limit(self):
        keys=tuple(Keyframe(i*100,40000 if i%2==0 else 50000) for i in range(8))
        self.assertCode(self.check(change_track(self.r,keyframes=keys)),'ANI_REVERSAL_LIMIT')
    def test_reduced_mode_motion_guard(self):
        modes=(replace(self.p.modes[0],kind='reduced'),)
        p=replace(self.p,modes=modes);r=replace(self.r,modes=modes)
        self.assertCode(self.check(r,p),'ANI_SPEED_LIMIT')
    def test_required_capture_missing(self):
        p=replace(self.p,captures=(replace(self.p.captures[0],required=True),))
        self.assertCode(self.check(p=p),'ANI_CAPTURE_MISSING')
    def test_disclosure_whole_transformation(self):
        p=replace(self.p,tracks=(replace(self.p.tracks[0],disclosure_cue_ids=('narration',)),)+self.p.tracks[1:])
        r=change_track(self.r,keyframes=(Keyframe(0,40000),Keyframe(2500,200000)))
        self.assertCode(self.check(r,p),'ANI_DISCLOSURE_TIMING')
    def test_disclosure_cover_ok(self):
        p=replace(self.p,tracks=(replace(self.p.tracks[0],disclosure_cue_ids=('narration',)),)+self.p.tracks[1:])
        self.assertNotIn('ANI_DISCLOSURE_TIMING',codes(self.check(p=p)))
    def test_unmapped_claim_is_blocker(self):
        s=self.p.tracks[0];p=replace(self.p,tracks=(replace(s,claim_ids=('different',)),)+self.p.tracks[1:])
        self.assertCode(self.check(p=p),'ANI_SOURCE_CLAIM_COVERAGE')
    def test_source_bytes_rechecked(self):
        (self.root/self.r.source.sources[0].artifact.path).write_text('modified')
        self.assertEqual(self.check().status,'BLOCKED')
    def test_source_output_bytes_rechecked(self):
        (self.root/self.r.source.outputs[0].artifact.path).write_text('modified')
        self.assertEqual(self.check().status,'BLOCKED')
    def test_empty_trust_is_not_default_approval(self):self.assertEqual(self.check(reviews=(),verifier=ReviewVerifier()).status,'REVIEW_REQUIRED')
    def test_native_contract_actually_called(self):self.assertEqual(len(self.check().native_diagnostics),1)
    def test_native_flags_not_promoted(self):self.assertFalse(self.check().product_accepted)
    def test_scene_snapshot_digest_changes_with_keyframe(self):
        r=change_track(self.r,keyframes=(Keyframe(0,40000),Keyframe(2000,210000)))
        self.assertNotEqual(r.plan_digest,self.r.plan_digest)
    def test_plan_digest_excludes_final_candidate_hash(self):
        r=replace(self.r,source=replace(self.r.source,candidate_digest='a'*64));self.assertEqual(r.plan_digest,self.r.plan_digest)
        self.assertNotEqual(r.content_digest,self.r.content_digest)
