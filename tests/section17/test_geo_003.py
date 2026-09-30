from batch003_helpers import Batch002Base,attach_fixture_tests,q
from fractions import Fraction
@attach_fixture_tests
class GEO003Tests(Batch002Base):
    task='BIE-EVAL-GEO-003'
    def test_global_budget_energy_conserved(self):
        d={'op':'planetary_budget','solar_constant_W_m2':1000,'albedo':'3/10','emissivity':1};v=self.values(d);self.assertEqual(Fraction(250),Fraction(v['absorbed_W_m2'])+Fraction(v['reflected_W_m2']));self.assertEqual('175',v['absorbed_W_m2'])
    def test_radiating_temperature_fourth_root_scaling(self):
        d={'op':'planetary_budget','solar_constant_W_m2':100,'albedo':0,'emissivity':1};t=self.values(d)['effective_radiating_temperature_K'];d['solar_constant_W_m2']=1600;self.assertAlmostEqual(2*t,self.values(d)['effective_radiating_temperature_K'])
    def test_water_depth_unit_equivalence(self):
        d={'op':'water_budget','precipitation':q(10,'cm'),'evapotranspiration':q(20,'mm'),'runoff':q('1/20','m')};self.assertEqual('30',self.values(d)['storage_change_mm'])
    def test_kelvin_and_celsius_same_mean(self):
        d={'op':'area_weighted_temperature','regions':[{'id':'a','area_km2':1,'temperature':q(0,'degC')},{'id':'b','area_km2':1,'temperature':q('5463/20','K')}]};self.assertEqual('0',self.values(d)['mean_degC'])
    def test_baseline_order_irrelevant(self):
        d=next(c.inputs for c in self.cases() if c.inputs.get('op')=='temperature_anomaly' and c.expected['status']=='OK');v=self.values(d);d['annual_means'].reverse();self.assertEqual(v,self.values(d))
    def test_thirty_rows_with_out_of_window_year_rejected(self):
        d=next(c.inputs for c in self.cases() if c.inputs.get('op')=='temperature_anomaly' and c.expected['status']=='OK');d['annual_means'][0]['year']=1800;self.rejected(d,'BASELINE_YEAR_GAP')
    def test_disconnected_cycles_not_one_feedback_loop(self):
        d={'op':'feedback_loop','links':[{'from':a,'to':b,'sign':'+'} for a,b in [('a','b'),('b','a'),('c','d'),('d','c')]]};self.rejected(d,'SIMPLE_CLOSED_LOOP_REQUIRED')
    def test_all_positive_cycle_reinforcing(self):
        d={'op':'feedback_loop','links':[{'from':'a','to':'b','sign':'+'},{'from':'b','to':'a','sign':'+'}]};self.assertEqual('reinforcing',self.values(d)['feedback'])
    def test_area_must_be_positive(self):
        d={'op':'area_weighted_temperature','regions':[{'id':'a','area_km2':0,'temperature':q(10,'degC')}]};self.rejected(d,'QUANTITY_OUT_OF_PROFILE')
    def test_no_surface_temperature_claim(self):
        v=self.values({'op':'planetary_budget','solar_constant_W_m2':1000,'albedo':0,'emissivity':1});self.assertNotIn('surface_temperature',v);self.assertIn('NOT_SURFACE',v['profile'])
