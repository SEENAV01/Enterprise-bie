from batch003_helpers import Batch002Base,attach_fixture_tests,q
from copy import deepcopy
import math
@attach_fixture_tests
class GEO002Tests(Batch002Base):
    task='BIE-EVAL-GEO-002'
    def test_scale_units_equivalent(self):
        d={'op':'scale_distance','map_length':q(1,'cm'),'scale_denominator':25000};v=self.values(d)
        d['map_length']=q(10,'mm');self.assertEqual(v,self.values(d));self.assertEqual('250',v['ground_m'])
    def test_area_scales_quadratically(self):
        d={'op':'scale_area','map_area':q(1,'m2'),'scale_denominator':100};self.assertEqual('10000',self.values(d)['ground_m2'])
        d['scale_denominator']=200;self.assertEqual('40000',self.values(d)['ground_m2'])
    def test_antimeridian_short_arc(self):
        d={'op':'spherical_distance','a':{'latitude_deg':0,'longitude_deg':179},'b':{'latitude_deg':0,'longitude_deg':-179},'sphere_radius_m':1}
        self.assertAlmostEqual(math.pi/90,self.values(d)['distance_m'],places=12)
    def test_distance_symmetric(self):
        d={'op':'spherical_distance','a':{'latitude_deg':-33,'longitude_deg':151},'b':{'latitude_deg':51,'longitude_deg':-1},'sphere_radius_m':6371000};v=self.values(d);d['a'],d['b']=d['b'],d['a'];self.assertEqual(v,self.values(d))
    def test_antipode_clamped_roundoff(self):
        d={'op':'spherical_distance','a':{'latitude_deg':0,'longitude_deg':0},'b':{'latitude_deg':0,'longitude_deg':180},'sphere_radius_m':10};self.assertAlmostEqual(10*math.pi,self.values(d)['distance_m'])
    def test_bearing_four_quadrants(self):
        for e,n,expected in ((0,1,0),(1,0,90),(0,-1,180),(-1,0,270)):
            self.assertEqual(expected,self.values({'op':'planar_bearing','delta_east_m':e,'delta_north_m':n})['bearing_deg'])
    def test_dms_boundary_and_hemisphere(self):
        d={'op':'dms','axis':'longitude','degrees':180,'minutes':0,'seconds':0,'hemisphere':'W'};self.assertEqual('-180',self.values(d)['decimal_degrees']);d['hemisphere']='S';self.rejected(d)
    def test_boolean_scale_not_number(self):
        self.rejected({'op':'scale_distance','map_length':q(1,'m'),'scale_denominator':True})
    def test_latitude_above_ninety_rejected(self):
        d={'op':'spherical_distance','a':{'latitude_deg':91,'longitude_deg':0},'b':{'latitude_deg':0,'longitude_deg':0},'sphere_radius_m':1};self.rejected(d)
    def test_no_silent_extra_fields(self):
        d=self.input();d['candidate_pass']=True;self.rejected(d)
