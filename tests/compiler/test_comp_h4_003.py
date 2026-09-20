from copy import deepcopy
from types import SimpleNamespace
import unittest
from bie.compiler.layout_measurements import *
from bie.compiler.layout_repair_contracts import canonical_scene
from tests.compiler.h4_test_support import scene,map_case,observation,TARGET_BIG

class OwnerMeasurementTests(unittest.TestCase):
    def setUp(self):
        p,_=map_case();self.raw=canonical_scene(p);self.fake=SimpleNamespace(effective_document=self.raw,codegen=SimpleNamespace(manifest_sha256='a'*64))
        self.m=observation(self.fake)
    def check(self):return inspect_owner_fit(self.m,self.raw,TARGET_BIG,'a'*64)
    def codes(self):return {f['code'] for f in self.check()['findings']}
    def test_complete_clear_measurement_passes(self):self.assertTrue(self.check()['passed'])
    def test_no_actual_render_or_release_claim(self):
        r=self.check();self.assertFalse(r['real_remotion_verified']);self.assertFalse(r['release_authorized']);self.assertFalse(r['accepted'])
    def test_owner_collision_is_detected(self):
        self.m['records'][0]['text_boxes'][1]['box']=self.m['records'][0]['text_boxes'][0]['box'];self.assertIn('LAYOUT_OWNER_TEXT_COLLISION',self.codes())
    def test_edge_touch_is_not_collision(self):self.assertFalse(overlap([0,0,10,10],[10,0,10,10]))
    def test_meaningful_overlap_is_collision(self):self.assertTrue(overlap([0,0,10,10],[8,0,10,10]))
    def test_subpixel_tolerance_not_content_tolerance(self):self.assertFalse(overlap([0,0,10,10],[9.5,0,10,10]))
    def test_duplicate_fragment_rejected(self):
        self.m['records'][0]['text_boxes'][1]['fragment_id']=self.m['records'][0]['text_boxes'][0]['fragment_id'];self.assertIn('LAYOUT_TEXT_FRAGMENT_DUPLICATE',self.codes())
    def test_missing_text_identity_rejected(self):
        self.m['records'][0]['text_boxes'][0].pop('text_id')
        with self.assertRaises(ValueError):self.check()
    def test_required_legend_cannot_disappear(self):
        self.m['records'][0]['rendered_text'].pop(1);self.assertIn('LAYOUT_VISIBLE_CONTENT_MISSING',self.codes())
    def test_required_attribution_cannot_disappear(self):
        self.m['records'][0]['rendered_text'].pop(-2);self.assertIn('LAYOUT_VISIBLE_CONTENT_MISSING',self.codes())
    def test_label_count_preserved(self):
        p,_=map_case();p['elements'][0]['props']['layers'][1]['label']=p['elements'][0]['props']['layers'][0]['label'];self.raw=canonical_scene(p);self.fake.effective_document=self.raw;self.m=observation(self.fake);self.m['records'][0]['rendered_text'].pop(2);self.assertIn('LAYOUT_VISIBLE_CONTENT_MISSING',self.codes())
    def test_exact_text_spaces_preserved(self):
        p=scene('text',{'text':'One  two\nthree'});self.raw=canonical_scene(p);self.fake.effective_document=self.raw;self.m=observation(self.fake);self.m['records'][0]['rendered_text']=['One two three'];self.assertIn('LAYOUT_VISIBLE_CONTENT_MISSING',self.codes())
    def test_empty_rendered_text_wrong_type_rejected(self):
        self.m['records'][0]['rendered_text']='some text'
        with self.assertRaises(ValueError):self.check()
    def test_missing_frame_cannot_pass(self):
        self.m['records'].pop();self.assertIn('LAYOUT_FRAME_COVERAGE_INCOMPLETE',self.codes())
    def test_wrong_scene_identity_rejected(self):
        self.m['scene_identity']='b'*64;self.assertIn('LAYOUT_EVIDENCE_IDENTITY_MISMATCH',self.codes())
    def test_wrong_manifest_identity_rejected(self):
        self.m['manifest_sha256']='b'*64;self.assertIn('LAYOUT_EVIDENCE_IDENTITY_MISMATCH',self.codes())
    def test_wrong_target_rejected(self):
        self.m['width']=640;self.assertIn('LAYOUT_EVIDENCE_IDENTITY_MISMATCH',self.codes())
    def test_claimed_real_remotion_scope_rejected(self):
        self.m['scope']='ACTUAL_REMOTION_ACCEPTED';self.assertIn('LAYOUT_EVIDENCE_SCOPE_UNTRUSTED',self.codes())
    def test_fonts_unready_blocks(self):
        self.m['fonts_ready']=False;self.assertIn('LAYOUT_FONTS_NOT_READY',self.codes())
    def test_browser_error_blocks(self):
        self.m['browser_errors']=['script failed'];self.assertIn('LAYOUT_BROWSER_ERROR',self.codes())
    def test_hidden_frame_not_required_to_show_legend(self):
        self.m['records'][0]['visible']=False;self.m['records'][0]['rendered_text']=[];self.assertTrue(self.check()['passed'])
    def test_full_content_fit_errors_retained(self):
        self.m['records'][0]['scroll_overflow']=True;self.assertIn('LAYOUT_CONTENT_OVERFLOW',self.codes())
    def test_invalid_rect_rejected(self):
        self.m['records'][0]['text_boxes'][0]['box']=[0,0,-1,10]
        with self.assertRaises(ValueError):self.check()
    def test_comparison_count_reported(self):self.assertGreater(self.check()['pair_comparisons'],0)

if __name__=='__main__':unittest.main()
