from vis_helpers import *
from bie.qa.visual_v2.evaluator import AREAS

class EvaluationTests(FixtureCase):
    def test_healthy_bounded_fixture(self):
        result=self.run_check();self.assertEqual(result.status,'CHECKS_PASSED');self.assertFalse(result.product_accepted)
        self.assertFalse(result.to_dict()['continuous_media_verified']);self.assertTrue(result.native_layout_fingerprints)
    def test_unsigned_requires_review(self):
        result=evaluate(self.request,self.root,self.policy,as_of=NOW);self.assertEqual(result.status,'REVIEW_REQUIRED')
    def test_deterministic_rerun(self):self.assertEqual(self.run_check().to_dict(),self.run_check().to_dict())
    def test_report_recompute_detects_edit(self):
        result=self.run_check();bad=replace(result,layout=replace(result.layout,measurements=(('states_checked',999),)))
        with self.assertRaises(ContractError):verify_reports(bad,self.request,self.root,self.policy,as_of=NOW,**options(self.request,self.policy))
    def test_source_bytes_changed(self):
        (self.root/'sources/authored-visual.txt').write_text('ALTERED')
        self.assertEqual(self.run_check().status,'BLOCKED')
    def test_output_bytes_changed(self):
        (self.root/'outputs/visual-text.txt').write_text('ALTERED')
        self.assertEqual(self.run_check().status,'BLOCKED')
    def test_source_missing(self):
        (self.root/'sources/authored-visual.txt').unlink();self.assertEqual(self.run_check().status,'BLOCKED')
    def test_unsupported_representation(self):
        r=replace(self.request,scenes=(replace(self.request.scenes[0],representation='text'),))
        self.assertCode(self.run_check(r), 'representation','VIS_REPRESENTATION_MISMATCH','BLOCKED')
    def test_missing_representation_feature(self):
        r=replace(self.request,scenes=(replace(self.request.scenes[0],features=()),))
        self.assertCode(self.run_check(r),'representation','VIS_REPRESENTATION_MISMATCH')
    def test_changed_objective(self):
        r=replace(self.request,scenes=(replace(self.request.scenes[0],objective_ids=('different-objective',)),))
        self.assertCode(self.run_check(r),'representation','VIS_REPRESENTATION_MISMATCH')
    def test_missing_required_state(self):
        s=replace(self.request.states[0],state_id='unauthorized-state')
        self.assertCode(self.run_check(replace(self.request,states=(s,))),'layout','VIS_STATE_SCOPE_MISMATCH')
    def test_missing_responsive_view(self):
        p=replace(self.policy,views=self.policy.views+(replace(self.policy.views[0],view_id='mobile'),),
            states=self.policy.states+(replace(self.policy.states[0],state_id='mobile-state',view_id='mobile'),))
        self.assertCode(self.run_check(p=p),'layout','VIS_STATE_SCOPE_MISMATCH')
    def test_changed_audience(self):
        self.assertCode(self.run_check(replace(self.request,audience_id='advanced')),'representation','VIS_SCOPE_CONTEXT_MISMATCH')
    def test_changed_language(self):
        self.assertCode(self.run_check(replace(self.request,language='hi')),'representation','VIS_SCOPE_CONTEXT_MISMATCH')
    def test_candidate_cannot_shorten_inventory(self):
        r=replace(self.request,elements=self.request.elements[:2])
        self.assertCode(self.run_check(r),'alignment','VIS_ELEMENT_SCOPE_MISMATCH')
    def test_unmapped_claim(self):
        es=change(self.request.elements,'object_id','object-3',claim_ids=('claim-1',))
        r=replace(self.request,elements=es);p=replace(self.policy,elements=es)
        self.assertCode(self.run_check(r,p),'alignment','VIS_UNMAPPED_SOURCE_CLAIM')
    def test_color_only_semantics(self):
        es=change(self.request.elements,'object_id','object-1',encodings=('color',))
        self.assertCode(self.run_check(replace(self.request,elements=es),replace(self.policy,elements=es)),'alignment','VIS_COLOR_ONLY_ENCODING')
    def test_missing_measurement_not_silently_dropped(self):
        s=replace(self.request.states[0],measurements=self.request.states[0].measurements[:2])
        self.assertCode(self.run_check(replace(self.request,states=(s,))),'layout','VIS_STATE_INVENTORY_MISMATCH')
    def test_changed_semantic_role(self):
        self.assertCode(self.run_check(replace(self.request,elements=change(self.request.elements,'object_id','object-1',role='shape'))),'alignment','VIS_ELEMENT_SPEC_CHANGED')
    def test_narration_is_not_screen_evidence(self):
        src=replace(self.request.source,outputs=(replace(self.request.source.outputs[0],channel='narration'),))
        self.assertCode(self.run_check(replace(self.request,source=src)),'alignment','VIS_TEXT_CHANNEL_MISMATCH')
    def test_false_text_cannot_pass_signed_review(self):
        self.assertCode(self.run_check(self.measured(text='There are seven counters.')),'alignment','VIS_DISPLAY_TEXT_MISMATCH')
    def test_role_label_cannot_bypass_text_readability(self):
        es=change(self.request.elements,'object_id','object-1',role='container')
        self.assertCode(self.run_check(replace(self.request,elements=es),replace(self.policy,elements=es)),'readability','VIS_TEXT_ROLE_BYPASS')
    def test_relation_reversal(self):
        rel=replace(self.request.relations[0],from_id='object-2',to_id='object-1')
        self.assertCode(self.run_check(replace(self.request,relations=(rel,)),replace(self.policy,relations=(rel,))),'alignment','VIS_SPATIAL_RELATION_VIOLATED')
    def test_relation_changed_cannot_redefine_operator(self):
        rel=replace(self.request.relations[0],kind='causes')
        self.assertCode(self.run_check(replace(self.request,relations=(rel,))),'alignment','VIS_RELATION_CHANGED_OR_UNBOUND')
    def test_hidden_relation_endpoint(self):self.assertCode(self.run_check(self.measured(displayed=False)),'alignment','VIS_RELATION_ENDPOINT_HIDDEN')
    def test_sample_not_continuous_proof(self):
        r=replace(self.request,states=(replace(self.request.states[0],geometry_mode='sampled'),))
        self.assertCode(self.run_check(r),'layout','VIS_CONTINUOUS_GEOMETRY_UNPROVEN','REVIEW_REQUIRED')
    def test_missing_capture_requires_review(self):self.assertCode(self.run_check(p=replace(self.policy,require_captures=True)),'layout','VIS_CAPTURE_REQUIRED','REVIEW_REQUIRED')
    def test_low_average_cannot_hide_one_bad_state(self):
        good=self.request.states[0];bad=replace(good,state_id='state-later',start_ms=20000,end_ms=21000)
        r=replace(self.request,states=(good,bad));p=replace(self.policy,states=self.policy.states+(replace(self.policy.states[0],state_id='state-later',start_ms=20000,end_ms=21000),))
        self.assertCode(self.run_check(r,p),'readability','VIS_TEXT_EXPOSURE_INSUFFICIENT')
    def test_local_density_not_global_average(self):self.assertCode(self.run_check(p=self.limit(max_cell_items=1,grid_rows=1,grid_columns=1)),'clutter','VIS_CLUTTER_LOCAL_DENSITY')
    def test_reading_rate_aggregates_simultaneous_text(self):
        # Individually all lines fit 130 codepoints/min; combined text does not.
        res=self.run_check(p=self.limit(max_read_codepoints_per_minute=130))
        self.assertNotIn('VIS_TEXT_EXPOSURE_INSUFFICIENT',codes(res.readability));self.assertCode(res,'clutter','VIS_CONCURRENT_READING_RATE')
    def test_known_text_white_on_white(self):self.assertCode(self.run_check(self.measured(foreground=RGBA(255,255,255))),'readability','VIS_CONTRAST_TOO_LOW')
    def test_445_contrast_not_rounded_to45(self):self.assertCode(self.run_check(self.measured(foreground=RGBA(119,119,119))),'readability','VIS_CONTRAST_TOO_LOW')
    def test_454_contrast_accepted(self):self.assertNotIn('VIS_CONTRAST_TOO_LOW',codes(self.run_check(self.measured(foreground=RGBA(118,118,118))).readability))
    def test_glyph_line_overflow_owner(self):self.assertCode(self.run_check(self.measured(line_boxes=(Rect(40000,40000,750000,30000),))),'readability','VIS_TEXT_OVERFLOW')
    def test_native_adapter_does_not_promote_acceptance(self):
        from bie.qa.visual_v2.adapters import to_native
        p,c=to_native(self.request,self.request.states[0],self.policy.views[0]);self.assertFalse(p.accepted);self.assertTrue(p.review_required);self.assertEqual(len(c),0)
    def test_wrapper_evaluators(self):
        from bie.qa.visual_v2 import evaluator
        for name,area in [('representation','representation'),('layout','layout'),('clutter','clutter'),('readability','readability'),('alignment','alignment')]:
            with self.subTest(area=area):
                self.assertEqual(getattr(evaluator,'evaluate_'+name)(self.request,self.root,self.policy,as_of=NOW,**options(self.request,self.policy)),getattr(self.run_check(),area))

# Each case changes a different safeguard and asserts the corresponding diagnosis.
MEASUREMENT_CASES={
 'hidden':({'displayed':False},'layout','VIS_REQUIRED_ELEMENT_HIDDEN'),
 'faded':({'opacity_ppm':500000},'layout','VIS_REQUIRED_ELEMENT_HIDDEN'),
 'offscreen':({'box':Rect(-5000,40000,600000,45000)},'layout','VIS_ELEMENT_CROPPED'),
 'clip':({'clip':Rect(0,0,500000,450000)},'layout','VIS_ELEMENT_CROPPED'),
 'safe_margin':({'box':Rect(1000,40000,600000,45000)},'layout','VIS_SAFE_AREA_OVERFLOW'),
 'subtitle_zone':({'box':Rect(40000,412000,600000,30000)},'layout','VIS_SUBTITLE_ZONE_COLLISION'),
 'collision':({'box':Rect(40000,135000,600000,45000)},'layout','VIS_LAYOUT_COLLISION'),
 'tiny_font':({'font_mpx':1000},'readability','VIS_FONT_TOO_SMALL'),
 'unloaded_font':({'fonts_loaded':False},'readability','VIS_FONTS_NOT_READY'),
 'missing_lines':({'line_boxes':()},'readability','VIS_TEXT_EXTENT_MISSING'),
 'unknown_background':({'background_known':False},'readability','VIS_CONTRAST_UNRESOLVED'),
 'transparent_background':({'background':RGBA(255,255,255,100)},'readability','VIS_CONTRAST_UNRESOLVED'),
 'alpha_foreground':({'foreground':RGBA(0,0,0,50)},'readability','VIS_CONTRAST_TOO_LOW'),
 'unsupported_transform':({'unsupported':('transform',)},'layout','VIS_UNSUPPORTED_GEOMETRY_OR_STYLE'),
}
for name,(changes,area,code) in MEASUREMENT_CASES.items():
 def test(self,changes=changes,area=area,code=code):self.assertCode(self.run_check(self.measured(**changes)),area,code)
 setattr(EvaluationTests,'test_measurement_'+name,test)
for name,kwargs,code in [('items',{'max_visible_items':2},'VIS_CLUTTER_ITEM_LIMIT'),('semantics',{'max_semantic_items':2},'VIS_CLUTTER_SEMANTIC_LIMIT'),('area',{'max_area_ppm':1},'VIS_CLUTTER_AREA_LIMIT'),('text',{'max_text_codepoints':1},'VIS_CLUTTER_TEXT_LIMIT')]:
 def test(self,kwargs=kwargs,code=code):self.assertCode(self.run_check(p=self.limit(**kwargs)),'clutter',code)
 setattr(EvaluationTests,'test_clutter_'+name,test)
