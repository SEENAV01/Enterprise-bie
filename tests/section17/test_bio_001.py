from batch002_helpers import Batch002Base, attach_fixture_tests, q, date
from copy import deepcopy
from fractions import Fraction

@attach_fixture_tests
class BIO001Tests(Batch002Base):
    task="BIE-EVAL-BIO-001"

    def test_net_budget_conserves_each_atom(self):
        for g in (0,1,3,'7/5',100):
            with self.subTest(g=g):
                v=self.values({'op':'net_budget','glucose_mol':g});g=Fraction(g)
                self.assertEqual(6*g,Fraction(v['net_consumed_mol']['CO2']))
                self.assertEqual(12*g,2*Fraction(v['net_consumed_mol']['H2O']))
                self.assertEqual(18*g,6*Fraction(v['net_produced_mol']['C6H12O6'])+2*Fraction(v['net_produced_mol']['O2']))
    def test_calvin_gross_equals_recycled_plus_export(self):
        for c in (0,1,3,12,'1/7'):
            v=self.values({'op':'calvin_budget','co2_mol':c})
            self.assertEqual(Fraction(v['gross_g3p_reduced_mol']),Fraction(v['g3p_recycled_mol'])+Fraction(v['net_g3p_mol']))
    def test_limiting_pools_never_overconsume(self):
        for c in (0,1,6):
            for a in (0,4,18):
                for n in (0,3,12):
                    v=self.values({'op':'resource_limited_calvin','co2_mol':c,'atp_mol':a,'nadph_mol':n});g=Fraction(v['net_g3p_mol'])
                    for key,feed,ratio in [('CO2',c,3),('ATP',a,9),('NADPH',n,6)]:
                        rest=Fraction(v['unused_mol'][key]);self.assertGreaterEqual(rest,0);self.assertEqual(feed,ratio*g+rest)
    def test_unknown_concept_cannot_improve_score(self):
        d=self.input(7);d['claims']['unknown_claim']=True
        self.assertIn({'claim':'unknown_claim','reason':'UNKNOWN_CLAIM'},self.values(d)['defects'])
    def test_boolean_is_not_quantity(self):self.rejected({'op':'net_budget','glucose_mol':True},'INVALID_RATIONAL')
    def test_quantity_upper_bound(self):self.rejected({'op':'calvin_budget','co2_mol':10**12+1},'QUANTITY_OUT_OF_PROFILE')
    def test_negative_supplied_pool(self):self.rejected({'op':'resource_limited_calvin','co2_mol':1,'atp_mol':-1,'nadph_mol':1})
    def test_boolean_concept_not_numeric_one(self):
        d=self.input(7);d['claims']['plants_also_respire']=1
        self.assertFalse(self.values(d)['consistent'])
    def test_expected_answer_injection_is_extra_field(self):
        d=self.input();d['expected']={'status':'PASS'};self.rejected(d,'INVALID_FIELDS')
    def test_input_and_reference_profile_not_mutated(self):
        d=self.input(7);before=deepcopy(d);v=self.values(d);v['defects'].append('injected');self.assertEqual(d,before);self.assertTrue(self.values(d)['consistent'])
