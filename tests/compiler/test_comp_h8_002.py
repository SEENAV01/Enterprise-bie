import unittest
from copy import deepcopy
import numpy as np
from bie.compiler.cartographic_qa import *
from tests.compiler.h8_test_support import mask,feature

class CartographicRasterTests(unittest.TestCase):
    def run_case(self,features,masks,**kw):return inspect_cartographic_masks(features,masks,**kw)
    def codes(self,r):return [f['code'] for f in r['findings']]
    def test_resolved_point(self):r=self.run_case([feature()],{'a':mask()});self.assertTrue(r['passed']);self.assertEqual(r['features'][0]['pixels'],25)
    def test_thin_point_reject(self):r=self.run_case([feature()],{'a':mask(box=(4,4,2,9))});self.assertIn('MAP_POINT_BELOW_PIXEL_FLOOR',self.codes(r))
    def test_no_point_ink(self):r=self.run_case([feature()],{'a':np.zeros((24,32),bool)});self.assertIn('MAP_FEATURE_NO_RESOLVED_INK',self.codes(r))
    def test_hidden_source_does_not_require_ink(self):r=self.run_case([feature(visible=False)],{'a':np.zeros((24,32),bool)});self.assertTrue(r['passed'])
    def test_small_polygon_reject(self):r=self.run_case([feature(kind='polygon')],{'a':mask(box=(2,2,1,10))});self.assertIn('MAP_POLYGON_COLLAPSED',self.codes(r))
    def test_resolved_polygon(self):self.assertTrue(self.run_case([feature(kind='polygon')],{'a':mask(box=(2,2,12,8))})['passed'])
    def test_short_route_reject(self):r=self.run_case([feature(kind='route')],{'a':mask(box=(2,2,3,1))});self.assertIn('MAP_ROUTE_COLLAPSED',self.codes(r))
    def test_resolved_thin_route(self):self.assertTrue(self.run_case([feature(kind='route')],{'a':mask(box=(2,2,15,1))})['passed'])
    def test_exact_duplicate_points(self):r=self.run_case([feature('a'),feature('b')],{'a':mask(),'b':mask()});self.assertIn('MAP_POINTS_VISUALLY_UNRESOLVED',self.codes(r))
    def test_separate_points(self):r=self.run_case([feature('a'),feature('b')],{'a':mask(),'b':mask(box=(18,14,5,5))});self.assertTrue(r['passed'])
    def test_near_point_policy(self):r=self.run_case([feature('a'),feature('b')],{'a':mask(),'b':mask(box=(10,4,5,5))});self.assertIn('MAP_POINTS_VISUALLY_UNRESOLVED',self.codes(r))
    def test_distinct_map_owners_not_confused(self):r=self.run_case([feature('a'),feature('b',owner='another')],{'a':mask(),'b':mask()});self.assertTrue(r['passed'])
    def test_identical_routes_rejected(self):r=self.run_case([feature('a',kind='route'),feature('b',kind='route')],{'a':mask(box=(2,6,25,2)),'b':mask(box=(2,6,25,2))});self.assertIn('MAP_ROUTES_VISUALLY_AMBIGUOUS',self.codes(r))
    def test_crossing_routes_not_identical_routes(self):r=self.run_case([feature('a',kind='route'),feature('b',kind='route')],{'a':mask(box=(2,6,25,2)),'b':mask(box=(14,2,2,18))});self.assertTrue(r['passed'])
    def test_point_route_intersection_not_point_duplicate(self):self.assertTrue(self.run_case([feature('a'),feature('b',kind='route')],{'a':mask(),'b':mask()})['passed'])
    def test_source_identity_retained(self):r=self.run_case([feature()],{'a':mask()});self.assertEqual(r['features'][0]['source_ref'],'fixture:map');self.assertEqual(r['features'][0]['layer_id'],'a')
    def test_no_universal_readability_claim(self):r=self.run_case([feature()],{'a':mask()});self.assertFalse(r['accepted']);self.assertIn('NOT_MAP_TRUTH',r['scope'])
    def test_empty_feature_set(self):self.assertTrue(self.run_case([],{})['passed'])
    def test_missing_mask(self):self.assertRaises(ValueError,self.run_case,[feature()],{})
    def test_extra_mask(self):self.assertRaises(ValueError,self.run_case,[],{'a':mask()})
    def test_duplicate_feature(self):self.assertRaises(ValueError,self.run_case,[feature(),feature()],{'a':mask()})
    def test_mask_dtypes(self):
        for a in (np.zeros((2,3),np.uint8),np.zeros((0,3),bool),np.zeros((2,3,4),bool)):
            with self.subTest(shape=a.shape),self.assertRaises(ValueError):self.run_case([feature()],{'a':a})
    def test_mask_size_mismatch(self):self.assertRaises(ValueError,self.run_case,[feature('a'),feature('b')],{'a':mask(),'b':np.zeros((20,20),bool)})
    def test_non_mapping_masks(self):self.assertRaises(ValueError,self.run_case,[],None)
    def test_unknown_fields(self):f=feature();f['passed']=True;self.assertRaises(ValueError,self.run_case,[f],{'a':mask()})
    def test_unknown_feature_kind(self):self.assertRaises(ValueError,self.run_case,[feature(kind='basemap')],{'a':mask()})
    def test_invalid_source(self):f=feature();f['source_ref']={};self.assertRaises(ValueError,self.run_case,[f],{'a':mask()})
    def test_policy_bounds(self):
        for k,v in [('min_point_diameter_px',True),('max_route_overlap',float('nan')),('point_separation_px',0)]:
            with self.subTest(k=k),self.assertRaises(ValueError):CartographicPolicy(**{k:v})
    def test_small_raster_and_large_separation_budget(self):
        r=self.run_case([feature('a'),feature('b')],{'a':np.ones((1,1),bool),'b':np.ones((1,1),bool)},policy=CartographicPolicy(point_separation_px=64));self.assertFalse(r['passed'])
