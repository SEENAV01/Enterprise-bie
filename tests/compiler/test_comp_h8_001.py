import unittest,tempfile,os,json
from pathlib import Path
from hashlib import sha256
from collections import deque
import numpy as np
from PIL import Image
from bie.compiler.raster_ink import *
from tests.compiler.h8_test_support import white,mask

class PixelContributionTests(unittest.TestCase):
    def images(self):
        b=white();a=b.copy();a[5:15,4:24]=0;return a,b,a.copy(),b.copy()
    def test_preserved_target_all_pixels_examined(self):
        a=self.images();r,m=counterfactual_ink(*a,target_id='x');self.assertTrue(r['passed']);self.assertEqual(r['pixel_count_inspected'],3072);self.assertEqual(r['visible_pixels'],200)
    def test_completely_covered_target_rejects(self):
        a,b,c,d=self.images();r,_=counterfactual_ink(b,b,c,b,target_id='x');self.assertFalse(r['passed']);self.assertEqual(r['visible_pixels'],0)
    def test_small_disconnected_missing_mark_is_not_lost_in_global_average(self):
        a,b,c,d=self.images();c[30,30:33]=0;a=c.copy();a[30,30:33]=255
        r,_=counterfactual_ink(a,b,c,b,target_id='math');self.assertGreater(r['visible_fraction'],.98);self.assertIn('RASTER_INK_COMPONENT_LOST',[f['code'] for f in r['findings']])
    def test_low_contribution_strength_detected(self):
        a,b,c,d=self.images();a[a==0]=200;r,_=counterfactual_ink(a,b,c,d,target_id='x');self.assertFalse(r['passed'])
    def test_deliberately_hidden_empty_frame_allowed(self):
        a=white();r,_=counterfactual_ink(a,a,a,a,target_id='hidden',originally_visible=False,require_nonempty=False);self.assertTrue(r['passed'])
    def test_required_white_on_white_rejected(self):
        a=white();r,_=counterfactual_ink(a,a,a,a,target_id='x');self.assertEqual(r['findings'][0]['code'],'RASTER_NO_DISTINGUISHABLE_INK')
    def test_hidden_target_paint_rejected(self):
        r,_=counterfactual_ink(*self.images(),target_id='x',originally_visible=False);self.assertIn('RASTER_HIDDEN_TARGET_PAINTS',[f['code'] for f in r['findings']])
    def test_no_opacity_strength_invention(self):
        b=white();a=b.copy();a[2:4,2:4]=245;r,_=counterfactual_ink(a,b,a,b,target_id='faint');self.assertTrue(r['passed']);self.assertEqual(r['expected_pixels'],4)
    def test_does_not_assign_unrelated_removed_occluder_pixels_to_target(self):
        a,b,c,d=self.images();a[25:30,25:30]=0;r,_=counterfactual_ink(a,b,c,d,target_id='x');self.assertEqual(r['expected_pixels'],200)
    def test_all_small_components_retained_in_report(self):
        b=white();a=b.copy();a[1,1]=0;a[3,3]=0;r,_=counterfactual_ink(a,b,a,b,target_id='x');self.assertEqual(len(r['components']),2)
    def test_diagonal_pixels_connected(self):
        a=np.eye(8,dtype=bool);r=connected_ink(a);self.assertEqual(len(r),1);self.assertEqual(r[0]['pixels'],8)
    def test_disjoint_runs_do_not_merge(self):
        a=np.zeros((4,8),bool);a[0,0:2]=True;a[2,4:6]=True;self.assertEqual(len(connected_ink(a)),2)
    def test_bridge_merges_two_parent_components(self):
        a=np.array([[1,0,0,0,1],[1,1,1,1,1]],bool);self.assertEqual(connected_ink(a)[0]['pixels'],7)
    def test_components_match_independent_flood_fill(self):
        rng=np.random.default_rng(112)
        for _ in range(40):
            m=rng.random((13,17))<.3;seen=np.zeros(m.shape,bool);areas=[]
            for y,x in zip(*np.nonzero(m)):
                if seen[y,x]:continue
                q=deque([(y,x)]);seen[y,x]=True;n=0
                while q:
                    yy,xx=q.popleft();n+=1
                    for dy in (-1,0,1):
                        for dx in (-1,0,1):
                            y2,x2=yy+dy,xx+dx
                            if 0<=y2<m.shape[0] and 0<=x2<m.shape[1] and m[y2,x2] and not seen[y2,x2]:seen[y2,x2]=True;q.append((y2,x2))
                areas.append(n)
            self.assertEqual(sorted(areas),sorted(r['pixels'] for r in connected_ink(m)))
    def test_component_run_budget_blocks_not_samples(self):
        with self.assertRaisesRegex(ValueError,'WORK_BUDGET'):connected_ink(np.eye(8,dtype=bool),max_runs=2)
    def test_invalid_visible_mask_rejected(self):
        for v in ([],np.zeros((2,2)),np.zeros((3,3),bool)):
            with self.subTest(v=type(v)),self.assertRaises(ValueError):connected_ink(np.ones((2,2),bool),v)
    def test_invalid_rgb_inputs(self):
        for a in (np.zeros((3,4)),np.zeros((3,4,3),np.float32),np.zeros((0,4,3),np.uint8)):
            with self.subTest(shape=a.shape),self.assertRaises(ValueError):counterfactual_ink(a,a,a,a,target_id='x')
    def test_image_shape_mismatch_rejected(self):
        a=self.images();a=(*a[:3],white(6,6));self.assertRaises(ValueError,counterfactual_ink,*a,target_id='x')
    def test_policy_invalid_values(self):
        for k,v in [('max_pixels',True),('pixel_delta',0),('min_visible_fraction',float('nan')),('max_runs',2000000),('min_visible_strength',-1)]:
            with self.subTest(k=k),self.assertRaises(ValueError):RasterPolicy(**{k:v})
    def test_no_acceptance_or_semantic_claim(self):
        r,_=counterfactual_ink(*self.images(),target_id='x');self.assertFalse(r['accepted']);self.assertIn('NOT_SEMANTIC',r['scope'])

class SecurePngTests(unittest.TestCase):
    def setUp(self):self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.p=self.root/'frame.png';Image.fromarray(white()).save(self.p)
    def tearDown(self):self.t.cleanup()
    def test_valid_rgb_hash_and_size(self):self.assertTrue(np.array_equal(read_png(self.p,expected_sha256=sha256(self.p.read_bytes()).hexdigest(),size=(64,48)),white()))
    def test_opaque_rgba_allowed(self):Image.new('RGBA',(8,9),(0,0,0,255)).save(self.p);self.assertEqual(read_png(self.p).shape,(9,8,3))
    def test_nonopaque_rejected(self):Image.new('RGBA',(8,9),(0,0,0,128)).save(self.p);self.assertRaisesRegex(ValueError,'OPAQUE',read_png,self.p)
    def test_tampered_hash_rejected(self):self.assertRaisesRegex(ValueError,'HASH',read_png,self.p,expected_sha256='0'*64)
    def test_size_mismatch(self):self.assertRaisesRegex(ValueError,'SIZE',read_png,self.p,size=(63,48))
    def test_symlink_file_rejected(self):p=self.root/'link.png';p.symlink_to(self.p);self.assertRaisesRegex(ValueError,'SYMLINK',read_png,p)
    def test_symlink_parent_rejected(self):p=self.root/'link';p.symlink_to(self.root,target_is_directory=True);self.assertRaisesRegex(ValueError,'SYMLINK',read_png,p/'frame.png')
    def test_fifo_is_nonblocking_rejected(self):p=self.root/'fifo';os.mkfifo(p);self.assertRaisesRegex(ValueError,'REGULAR',read_png,p)
    def test_directory_rejected(self):self.assertRaisesRegex(ValueError,'REGULAR',read_png,self.root)
    def test_missing_rejected(self):self.assertRaisesRegex(ValueError,'UNAVAILABLE',read_png,self.root/'missing')
    def test_zero_byte_rejected(self):self.p.write_bytes(b'');self.assertRaisesRegex(ValueError,'BYTE',read_png,self.p)
    def test_byte_budget(self):self.assertRaisesRegex(ValueError,'BYTE',read_png,self.p,policy=RasterPolicy(max_bytes=10))
    def test_pixel_budget(self):self.assertRaisesRegex(ValueError,'PIXEL',read_png,self.p,policy=RasterPolicy(max_pixels=100))
    def test_non_png_rejected(self):Image.new('RGB',(5,5)).save(self.p,format='JPEG');self.assertRaisesRegex(ValueError,'PNG',read_png,self.p)
    def test_palette_rejected(self):Image.new('P',(5,5)).save(self.p);self.assertRaisesRegex(ValueError,'RGB',read_png,self.p)
    def test_corrupt_bytes(self):self.p.write_bytes(b'not a png');self.assertRaisesRegex(ValueError,'DECODE',read_png,self.p)
    def test_icc_requires_trusted_normalization(self):Image.new('RGB',(5,5)).save(self.p,icc_profile=b'test-profile');self.assertRaisesRegex(ValueError,'COLOR_PROFILE',read_png,self.p)
    def test_truncated_image_rejected(self):self.p.write_bytes(self.p.read_bytes()[:40]);self.assertRaises(ValueError,read_png,self.p)
