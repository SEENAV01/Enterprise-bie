from copy import deepcopy
import unittest
from bie.compiler.content_fit_qa import *
from tests.compiler.h3_test_support import scene,measurement,TARGET
class ContentFitTests(unittest.TestCase):
    def setUp(self):self.p=scene(duration_ms=100);self.r=measurement(self.p)
    def check(self):return inspect_content_fit(self.r,self.p,TARGET,'a'*64)
    def codes(self):return {f['code'] for f in self.check()['findings']}
    def test_complete_observations_pass(self):self.assertTrue(self.check()['passed'])
    def test_missing_middle_frame_blocks(self):self.r['records'].pop(1);self.assertIn('LAYOUT_FRAME_COVERAGE_INCOMPLETE',self.codes())
    def test_duplicate_frame_blocks(self):self.r['records'][1]=deepcopy(self.r['records'][0]);self.assertIn('LAYOUT_FRAME_DUPLICATE',self.codes())
    def test_unknown_element_blocks(self):self.r['records'][0]['element_id']='absent';self.assertIn('LAYOUT_FRAME_UNKNOWN',self.codes())
    def test_out_of_range_frame_blocks(self):self.r['records'][0]['frame']=99;self.assertIn('LAYOUT_FRAME_UNKNOWN',self.codes())
    def test_stale_manifest_blocks(self):self.r['manifest_sha256']='b'*64;self.assertIn('LAYOUT_EVIDENCE_IDENTITY_MISMATCH',self.codes())
    def test_stale_scene_blocks(self):self.r['scene_identity']='b'*64;self.assertFalse(self.check()['passed'])
    def test_wrong_viewport_blocks(self):self.r['width']=1280;self.assertFalse(self.check()['passed'])
    def test_wrong_fps_blocks(self):self.r['fps']=25;self.assertFalse(self.check()['passed'])
    def test_boolean_frame_count_blocks(self):self.r['frame_count']=True;self.assertFalse(self.check()['passed'])
    def test_fonts_unready_blocks(self):self.r['fonts_ready']=False;self.assertIn('LAYOUT_FONTS_NOT_READY',self.codes())
    def test_browser_error_blocks(self):self.r['browser_errors']=['paint exception'];self.assertIn('LAYOUT_BROWSER_ERROR',self.codes())
    def test_overflow_blocks(self):self.r['records'][0]['scroll_overflow']=True;self.assertIn('LAYOUT_CONTENT_OVERFLOW',self.codes())
    def test_long_legend_outside_owner_blocks(self):self.r['records'][0]['text_boxes'][0]['box']=[60,60,300,20];self.assertIn('LAYOUT_TEXT_OUTSIDE_OWNER',self.codes())
    def test_small_text_blocks(self):self.r['records'][0]['text_boxes'][0]['font_px']=6;self.assertIn('LAYOUT_TEXT_BELOW_MINIMUM',self.codes())
    def test_small_equation_blocks(self):self.r['records'][0]['equation_em_px']=5;self.assertIn('LAYOUT_EQUATION_BELOW_MINIMUM',self.codes())
    def test_ink_outside_viewport_blocks(self):self.r['records'][0]['ink_boxes']=[[-100,50,50,30]];self.assertIn('LAYOUT_INK_OUTSIDE_VIEWPORT',self.codes())
    def test_negative_rectangle_rejected(self):
        self.r['records'][0]['ink_boxes']=[[1,2,-3,4]]
        with self.assertRaises(ValueError):self.check()
    def test_nonfinite_measurement_rejected(self):
        self.r['records'][0]['text_boxes'][0]['font_px']=float('inf')
        with self.assertRaises(ValueError):self.check()
    def test_malformed_visibility_rejected(self):
        self.r['records'][0]['visible']='false'
        with self.assertRaises(ValueError):self.check()
    def test_fade_hidden_frame_excluded_from_readability(self):
        self.r['records'][0]['visible']=False;self.r['records'][0]['text_boxes'][0]['font_px']=0;self.assertTrue(self.check()['passed'])
    def test_forged_real_scope_not_trusted(self):self.r['scope']='REAL_REMOTION';self.assertIn('LAYOUT_EVIDENCE_SCOPE_UNTRUSTED',self.codes())
    def test_external_measurements_explicitly_not_attested(self):
        self.r['scope']=DECLARED_SCOPE;v=self.check();self.assertTrue(v['passed']);self.assertFalse(v['release_authorized'])
    def test_bridge_cannot_authorize_release(self):
        with self.assertRaisesRegex(ValueError,'REAL_LAYOUT_EVIDENCE_REQUIRED'):require_real_layout_authorization(self.check())
    def test_equation_floor_is_explicit_policy(self):
        self.p['metadata']['compiler_h3']={'layout':{'min_equation_px':30}};self.r=measurement(self.p);self.r['records'][0]['equation_em_px']=25;self.assertIn('LAYOUT_EQUATION_BELOW_MINIMUM',self.codes())
    def test_content_not_rewritten_by_check(self):
        old=deepcopy(self.p);self.check();self.assertEqual(old,self.p)
    def test_evidence_hash_changes_on_measurement(self):
        a=self.check();self.r['records'][0]['text_boxes'][0]['font_px']=17;self.assertNotEqual(a['evidence_sha256'],self.check()['evidence_sha256'])
if __name__=='__main__':unittest.main()
