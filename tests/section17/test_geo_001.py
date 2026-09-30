from batch002_helpers import Batch002Base, attach_fixture_tests, q, date
from copy import deepcopy
from fractions import Fraction

@attach_fixture_tests
class GEO001Tests(Batch002Base):
    task="BIE-EVAL-GEO-001"

    def test_plate_swap_and_normal_reversal_preserve_separation(self):
        d=self.input();v=self.values(d);d['velocity_a'],d['velocity_b']=d['velocity_b'],d['velocity_a'];d['normal_a_to_b']=[str(-Fraction(n)) for n in d['normal_a_to_b']];self.assertEqual(v,self.values(d))
    def test_common_translation_does_not_change_relative_motion(self):
        d=self.input();v=self.values(d)
        for k in ('velocity_a','velocity_b'):d[k]['values']=[str(Fraction(x)+7) for x in d[k]['values']]
        self.assertEqual(v,self.values(d))
    def test_rational_unit_normal_projection(self):
        d={'op':'boundary_motion','velocity_a':{'values':[0,0],'unit':'cm/yr'},'velocity_b':{'values':[3,4],'unit':'cm/yr'},'normal_a_to_b':['3/5','4/5']};v=self.values(d);self.assertEqual('5',v['separation_cm_per_yr']);self.assertEqual('0',v['tangential_cm_per_yr'])
    def test_mm_and_cm_rate_equivalence(self):
        d={'op':'spreading_distance','rate':q(3,'cm/yr'),'rate_kind':'half','duration':q(2,'Myr')};v=self.values(d);d['rate']=q(30,'mm/yr');d['duration']=q(2000000,'yr');self.assertEqual(v,self.values(d))
    def test_spreading_age_round_trip(self):
        for rate in (1,3,'7/2'):
            d={'op':'spreading_distance','rate':q(rate,'cm/yr'),'rate_kind':'half','duration':q('3/2','Myr')};v=self.values(d);age=self.values({'op':'age_from_ridge','distance':q(v['one_flank_km'],'km'),'half_rate':q(rate,'cm/yr')});self.assertEqual('3/2',age['age_Myr'])
    def test_zero_relative_velocity_not_transform(self):
        d=self.input();d['velocity_b']=deepcopy(d['velocity_a']);self.assertEqual('no_relative_motion',self.values(d)['motion'])
    def test_negative_duration_refused(self):
        d=self.input(4);d['duration']=q(-1,'Myr');self.rejected(d,'QUANTITY_OUT_OF_PROFILE')
    def test_approximate_normal_not_silently_normalized(self):
        d=self.input();d['normal_a_to_b']=[0.707,0.707];self.rejected(d,'EXACT_UNIT_NORMAL_REQUIRED')
    def test_transform_motion_has_no_crust_prediction_score(self):
        v=self.values({'op':'boundary_features','boundary':'transform'});self.assertNotIn('earthquake_probability',v)
    def test_subduction_class_does_not_deny_all_new_crust(self):
        v=self.values({'op':'boundary_features','boundary':'ocean_continent_convergent'});self.assertNotIn('crust_created',v);self.assertTrue(v['oceanic_lithosphere_consumed'])
