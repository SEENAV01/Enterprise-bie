from batch004_helpers import DeliveryMetricBase,attach
from bie.evaluation.benchmarks.metrics.animation import interpolate
from fractions import Fraction
@attach
class METRIC010Tests(DeliveryMetricBase):
    task='BIE-EVAL-METRIC-010'
    def test_nonmonotonic_samples_blocked(self):
        r,c,a=self.example();c['tracks'][0]['samples'][1]['frame']=0;self.reject(r,c,a,code='NONINCREASING_SAMPLE_FRAME')
    def test_fractional_midpoint_is_exact(self):self.assertEqual(Fraction(1,2),interpolate([(0,Fraction(0)),(10,Fraction(1))],5))
    def test_incomplete_reference_knot_roster_blocked(self):
        r,c,a=self.example();r['payload']['tracks'][0]['knots'][0]['frame']=1;self.reject(r,c,a,code='REFERENCE_KNOT_COVERAGE_MISSING')
    def test_reference_speed_self_inconsistent_blocked(self):
        r,c,a=self.example();r['payload']['tracks'][0]['max_speed']=1;self.reject(r,c,a,code='REFERENCE_DYNAMICS_OUT_OF_BOUNDS')
    def test_reference_endpoints_required(self):
        r,c,a=self.example();r['payload']['sample_frames']=[1,5,10];self.reject(r,c,a,code='INVALID_REFERENCE_SAMPLE_ROSTER')
    def test_duplicate_reference_sample_blocked(self):
        r,c,a=self.example();r['payload']['sample_frames']=[0,5,5,10];self.reject(r,c,a,code='INVALID_REFERENCE_SAMPLE_ROSTER')
    def test_reference_bounds_reversed_blocked(self):
        r,c,a=self.example();r['payload']['tracks'][0]['minimum']=20;self.reject(r,c,a,code='REFERENCE_TRAJECTORY_OUT_OF_BOUNDS')
    def test_wrong_property_fails(self):
        r,c,a=self.example();c['tracks'][0]['property']='opacity';self.fail_reason(r,c,a,'PROPERTY_OR_UNIT_MISMATCH')
    def test_nan_sample_rejected(self):
        r,c,a=self.example();c['tracks'][0]['samples'][1]['value']=float('nan');self.reject(r,c,a)
    def test_acceleration_check_catches_jitter(self):
        r,c,a=self.example();c['tracks'][0]['samples'][1]['value']=4;self.fail_reason(r,c,a,'ACCELERATION_BOUND_EXCEEDED')
