import unittest
from copy import deepcopy
from dataclasses import replace
from bie.compiler.media_presentation import image_geometry,media_presentations
from bie.compiler.media_compiler import compile_image_or_video_element
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.scene_ir.image_element import build
from tests.compiler.h11_test_support import scene,asset,T

class ImageCropPresentation(unittest.TestCase):
    def geom(self,p=None):
        p=p or scene('crop-image');return image_geometry(p['elements'][0],asset(p),T)
    def bad(self,change,code):
        p=scene('crop-image');change(p['elements'][0]['props']);self.assertRaisesRegex(ValueError,code,self.geom,p)
    def test_exact_source_rectangle(self):self.assertEqual(self.geom()['source_crop'],[48,0,48,32])
    def test_contain_keeps_aspect(self):
        g=self.geom();self.assertAlmostEqual(g['crop_viewport'][0]/g['crop_viewport'][1],1.5)
    def test_crop_no_larger_than_owner(self):
        g=self.geom();self.assertLessEqual(g['crop_viewport'][0],g['viewport'][0]);self.assertLessEqual(g['crop_viewport'][1],g['viewport'][1])
    def test_normalized_and_pixel_rectangles_equivalent(self):
        p=scene('crop-image');p['elements'][0]['props'].update(crop=[48,0,48,32],crop_space='source-pixels-xywh');self.assertEqual(self.geom(p),self.geom())
    def test_crop_space_required(self):self.bad(lambda p:p.pop('crop_space'),'CROP_SPACE_REQUIRED')
    def test_crop_outside_bounds(self):self.bad(lambda p:p.update(crop=[.5,0,.6,.5]),'OUT_OF_BOUNDS')
    def test_zero_area_not_allowed(self):self.bad(lambda p:p.update(crop=[0,0,0,1]),'OUT_OF_BOUNDS')
    def test_negative_crop_not_allowed(self):self.bad(lambda p:p.update(crop=[-.1,0,.5,.5]),'OUT_OF_BOUNDS')
    def test_boolean_and_nonfinite_not_numbers(self):
        for v in [True,float('inf'),float('nan')]:
            with self.subTest(v=v):self.bad(lambda p:p.update(crop=[v,0,.5,.5]),'CROP_INVALID')
    def test_unknown_prop_not_ignored(self):self.bad(lambda p:p.update(rotation=30),'PROPERTY_UNCONSUMED')
    def test_implicit_cover_not_allowed(self):self.bad(lambda p:p.update(fit='cover'),'FIT_UNSUPPORTED')
    def test_original_image_builder_names_crop_units(self):
        e=build('e','a',['s'],['r'],'rights','alt',crop=[0,0,.5,.5]);self.assertEqual(e.props['crop_space'],'normalized-xywh')
    def test_legacy_direct_crop_cannot_be_ignored(self):self.assertRaisesRegex(ValueError,'CROP_BINDING_REQUIRED',compile_image_or_video_element,scene('crop-image')['elements'][0])
    def test_verified_codegen_crops_and_keeps_alternative_text(self):
        p=scene('crop-image');binding=media_presentations(p,T)['rows'][0];s=compile_image_or_video_element(p['elements'][0],presentation=binding).source_text
        self.assertIn('data-bie-source-crop',s);self.assertIn('aria-label',s);self.assertIn('CanvasImage',s);self.assertIn('overflow',s)
    def test_different_crops_produce_different_generated_bytes(self):
        p=scene('crop-image');a=compile_h3_scene(p,target=T);p['elements'][0]['props']['crop']=[0,0,.5,.5];b=compile_h3_scene(p,target=T);self.assertNotEqual(a.codegen.manifest_sha256,b.codegen.manifest_sha256)
    def test_source_file_bytes_not_rewritten(self):
        p=scene('crop-image');b=compile_h3_scene(p,target=T);self.assertEqual(b.bundle.element_results[0].asset_paths,(asset(p)['public_path'],))
    def test_wider_viewport_does_not_distort_image(self):
        p=scene();g=image_geometry(p['elements'][0],asset(p),replace(T,width=1920));self.assertEqual(g['image_size'][0]/g['image_size'][1],1.5)
    def test_unbound_crop_space_rejected(self):
        p=scene();p['elements'][0]['props']['crop_space']='normalized-xywh';self.assertRaisesRegex(ValueError,'CROP_WITHOUT_RECT',self.geom,p)
