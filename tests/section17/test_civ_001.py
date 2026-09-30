from batch003_helpers import Batch002Base,attach_fixture_tests
from bie.evaluation.benchmarks.domains.civics import PROFILE,ROLES
@attach_fixture_tests
class CIV001Tests(Batch002Base):
    task='BIE-EVAL-CIV-001'
    def roles(self,claims):return self.values({'op':'audit_roles','profile':PROFILE,'claims':claims})
    def trace(self,events):return self.values({'op':'ordinary_bill_trace','profile':PROFILE,'route':'ordinary_two_house_bill','events':events})
    def test_omission_not_assumed_correct(self):
        v=self.roles({});self.assertEqual(5,len(v['defects']))
    def test_unknown_claim_not_ignored(self):
        d=dict(ROLES);d['party_best']='x';v=self.roles(d);self.assertTrue(v['defects']);self.assertNotIn('political_score',v)
    def test_integer_one_not_boolean_true(self):
        d=dict(ROLES);d['ministers_can_also_sit_in_parliament']=1;self.assertTrue(self.roles(d)['defects'])
    def test_assent_after_only_one_house_not_act(self):
        v=self.trace(['introduced','commons_agreed','royal_assent']);self.assertFalse(v['act_in_this_profile'])
    def test_agreement_without_introduction_not_valid(self):
        self.assertFalse(self.trace(['commons_agreed','lords_agreed','royal_assent'])['trace_consistent'])
    def test_assent_then_house_not_valid(self):
        self.assertFalse(self.trace(['introduced','commons_agreed','royal_assent','lords_agreed'])['trace_consistent'])
    def test_same_fictional_power_can_belong_to_two_institutions(self):
        d={'op':'fictional_competence','jurisdiction':'FICTIONAL_EDUCATIONAL_SCENARIO','institutions':[{'id':'a','powers':['p']},{'id':'b','powers':['p']}],'request':{'institution':'b','power':'p'}};self.assertTrue(self.values(d)['assigned_in_supplied_scenario'])
    def test_real_jurisdiction_not_inferred_for_fictional_rules(self):
        d={'op':'fictional_competence','jurisdiction':'UK','institutions':[{'id':'a','powers':['p']}],'request':{'institution':'a','power':'p'}};self.rejected(d)
    def test_duplicate_fictional_powers_rejected(self):
        d={'op':'fictional_competence','jurisdiction':'FICTIONAL_EDUCATIONAL_SCENARIO','institutions':[{'id':'a','powers':['p','p']}],'request':{'institution':'a','power':'p'}};self.rejected(d)
    def test_unsupported_special_bill_route_rejected(self):
        d={'op':'ordinary_bill_trace','profile':PROFILE,'route':'special_money_bill','events':['introduced','royal_assent']};self.rejected(d)
