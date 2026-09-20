import unittest,tempfile,json
from pathlib import Path
from copy import deepcopy
from dataclasses import replace
from PIL import Image
from bie.compiler.raster_capture import *
from tests.compiler.h8_test_support import *

class CaptureContractTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.raw=raw_text();self.capture=capture_fixture(self.root,self.raw)
    def tearDown(self):self.t.cleanup()
    def inspect(self,c=None,**kw):return inspect_counterfactual_capture(self.root,c or self.capture,self.raw,SMALL,'a'*64,expected_scope=DIAGNOSTIC_SCOPE,**kw)
    def test_complete_capture_passes_but_not_release(self):
        r=self.inspect();self.assertTrue(r['passed']);self.assertFalse(r['accepted']);self.assertFalse(r['release_authorized']);self.assertEqual(r['frame_count'],2);self.assertEqual(r['image_count'],10)
    def test_required_all_frames(self):self.capture['frames'].pop();self.assertRaisesRegex(ValueError,'FRAME_COVERAGE',self.inspect)
    def test_reversed_frames(self):self.capture['frames'].reverse();self.assertRaisesRegex(ValueError,'FRAME_IDENTITY',self.inspect)
    def test_duplicate_frame(self):self.capture['frames'][1]['frame']=0;self.assertRaisesRegex(ValueError,'FRAME_IDENTITY',self.inspect)
    def test_wrong_source(self):self.capture['scene_sha256']='b'*64;self.assertRaisesRegex(ValueError,'SOURCE_IDENTITY',self.inspect)
    def test_wrong_generated_manifest(self):self.capture['manifest_sha256']='b'*64;self.assertRaisesRegex(ValueError,'SOURCE_IDENTITY',self.inspect)
    def test_fake_real_scope_rejected_in_diagnostic_consumer(self):self.capture['scope']=REAL_SCOPE;self.assertRaisesRegex(ValueError,'SCOPE_MISMATCH',self.inspect)
    def test_cannot_pass_diagnostic_capture_to_real_consumer(self):self.assertRaisesRegex(ValueError,'SCOPE_MISMATCH',inspect_counterfactual_capture,self.root,self.capture,self.raw,SMALL,'a'*64,expected_scope=REAL_SCOPE)
    def test_unknown_scope(self):self.assertRaisesRegex(ValueError,'SCOPE_INVALID',inspect_counterfactual_capture,self.root,self.capture,self.raw,SMALL,'a'*64,expected_scope='generic')
    def test_wrong_resolution(self):self.capture['width']+=1;self.assertRaisesRegex(ValueError,'DIMENSIONS',self.inspect)
    def test_boolean_frame_count(self):self.capture['frame_count']=True;self.assertRaisesRegex(ValueError,'DIMENSIONS',self.inspect)
    def test_browser_error_rejected(self):self.capture['browser_errors']=['Uncaught'];self.assertRaisesRegex(ValueError,'BROWSER_ERRORS',self.inspect)
    def test_undeclared_capture_field(self):self.capture['accepted']=True;self.assertRaisesRegex(ValueError,'FIELDS',self.inspect)
    def test_inventory_missing(self):self.capture['frames'][0]['inventory']=[];self.assertRaisesRegex(ValueError,'INVENTORY_COVERAGE',self.inspect)
    def test_inventory_swapped_target(self):self.capture['frames'][0]['inventory'][0]['target_id']='other';self.assertRaisesRegex(ValueError,'INVENTORY_IDENTITY',self.inspect)
    def test_inventory_nan(self):self.capture['frames'][0]['inventory'][0]['box'][0]=float('nan');self.assertRaisesRegex(ValueError,'INVENTORY_INVALID',self.inspect)
    def test_inventory_effect_not_passed(self):self.capture['frames'][0]['inventory'][0]['unresolved_effect']=True;r=self.inspect();self.assertFalse(r['passed']);self.assertIn('RASTER_EFFECT_ATTRIBUTION_UNVERIFIED',[f['code'] for f in r['findings']])
    def test_missing_target_images(self):self.capture['frames'][0]['targets']=[];self.assertRaisesRegex(ValueError,'TARGET_COVERAGE',self.inspect)
    def test_path_traversal_not_opened(self):self.capture['frames'][0]['full']['file']='../outside.png';self.assertRaisesRegex(ValueError,'IMAGE_IDENTITY',self.inspect)
    def test_frame_image_substitution(self):self.capture['frames'][0]['full']=deepcopy(self.capture['frames'][1]['full']);self.assertRaisesRegex(ValueError,'IMAGE_IDENTITY',self.inspect)
    def test_mutated_image_bytes(self):p=self.root/self.capture['frames'][0]['full']['file'];p.write_bytes(p.read_bytes()+b'junk');self.assertRaisesRegex(ValueError,'HASH',self.inspect)
    def test_restore_mismatch_not_silently_tolerated(self):
        r=self.capture['frames'][0];r['repeat']=save_png(self.root,r['repeat']['file'],white());self.assertRaisesRegex(ValueError,'DID_NOT_RESTORE',self.inspect)
    def test_restore_hash_does_not_make_wrong_pixels_safe(self):
        r=self.capture['frames'][0];a=white();a[0,0]=0;r['repeat']=save_png(self.root,r['repeat']['file'],a);self.assertRaises(ValueError,self.inspect)
    def test_missing_png(self):(self.root/self.capture['frames'][0]['full']['file']).unlink();self.assertRaisesRegex(ValueError,'UNAVAILABLE',self.inspect)
    def test_capture_symlink_root(self):
        link=self.root/'link';link.symlink_to(self.root);self.assertRaisesRegex(ValueError,'SYMLINK',inspect_counterfactual_capture,link,self.capture,self.raw,SMALL,'a'*64,expected_scope=DIAGNOSTIC_SCOPE)
    def test_synthetic_occlusion_rejected(self):
        r=self.capture['frames'][0];a=white();r['full']=save_png(self.root,r['full']['file'],a);r['repeat']=save_png(self.root,r['repeat']['file'],a);self.assertFalse(self.inspect()['passed'])
    def test_map_target_source_list(self):
        t=build_raster_targets(map_scene());self.assertEqual([r['target_id'] for r in t],['owner:0','map:0:0','map:0:1']);self.assertEqual(t[1]['layer_id'],'p0')
    def test_duplicate_element_id(self):p=raw_text();p['elements'].append(deepcopy(p['elements'][0]));self.assertRaisesRegex(ValueError,'IDENTITY',build_raster_targets,p)
    def test_budget_never_samples(self):self.assertRaisesRegex(ValueError,'NO_SAMPLED_PASS',capture_budget,1920,1080,2400,8)
    def test_budget_boolean(self):self.assertRaises(ValueError,capture_budget,True,10,1,1)
    def test_filename_exact_and_bounded(self):self.assertEqual(frame_file(4,'muted',2),'frame-000004-target-002-muted.png');self.assertRaises(ValueError,frame_file,-1,'full');self.assertRaises(ValueError,frame_file,0,'bad');self.assertRaises(ValueError,frame_file,0,'muted')
    def test_required_blank_source(self):self.assertFalse(required_paint(raw_text('   '),SMALL,0)['e0'])
    def test_required_text_visible(self):self.assertTrue(required_paint(self.raw,SMALL,0)['e0'])
    def test_fade_zero_frame_does_not_need_ink(self):
        p=raw_text(duration_ms=1000);p['tracks']=[track('enter',{},element_id='e0',end_ms=1000)];self.assertFalse(required_paint(p,SMALL,0)['e0']);self.assertTrue(required_paint(p,SMALL,3)['e0'])
