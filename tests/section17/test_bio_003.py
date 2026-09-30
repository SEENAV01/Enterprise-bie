from batch002_helpers import Batch002Base, attach_fixture_tests, q, date
from copy import deepcopy
from fractions import Fraction

@attach_fixture_tests
class BIO003Tests(Batch002Base):
    task="BIE-EVAL-BIO-003"

    def test_frequency_and_volume_unit_equivalence(self):
        a=self.values({'op':'cardiac_output','stroke_volume':q(80,'mL'),'heart_rate':q(60,'per_min')})
        b=self.values({'op':'cardiac_output','stroke_volume':q('2/25','L'),'heart_rate':q(1,'per_s')});self.assertEqual(a,b);self.assertEqual('24/5',a['cardiac_output_L_per_min'])
    def test_osmolar_unit_equivalence(self):
        d={'op':'osmosis','inside':q(300,'mOsm/L'),'outside':q('3/10','Osm/L'),'solute_profile':'nonpenetrating_ideal'};self.assertEqual('no_net_flow',self.values(d)['water_direction'])
    def test_permeating_solute_not_silently_tonicity(self):
        d=self.input(6);d['solute_profile']='freely_permeating';self.rejected(d,'UNSUPPORTED_ENUM')
    def test_zero_rate_means_zero_model_flow_not_diagnosis(self):
        d=self.input();d['heart_rate']=q(0,'per_min');v=self.values(d);self.assertEqual('0',v['cardiac_output_L_per_min']);self.assertNotIn('diagnosis',v)
    def test_negative_volume_refused(self):
        d=self.input();d['stroke_volume']=q(-1,'mL');self.rejected(d,'QUANTITY_OUT_OF_PROFILE')
    def test_converted_volume_bound_checked(self):
        d=self.input();d['stroke_volume']=q(10**12,'L');self.rejected(d,'QUANTITY_OUT_OF_PROFILE')
    def test_no_unit_guessing(self):
        d=self.input();d['stroke_volume']={'value':75};self.rejected(d,'INVALID_FIELDS')
    def test_route_return_is_defensive_copy(self):
        d={'op':'circulation_route','circuit':'pulmonary'};v=self.values(d);v['route'][0]='bad';self.assertEqual('right_ventricle',self.values(d)['route'][0])
    def test_fetal_circuit_outside_scope(self):self.rejected({'op':'circulation_route','circuit':'fetal'},'UNSUPPORTED_ENUM')
    def test_float_nan_stopped_at_json_boundary(self):
        from bie.evaluation.benchmarks.models import BenchmarkError
        d=self.input();d['stroke_volume']['value']=float('nan')
        with self.assertRaises(BenchmarkError):self.result(d)
