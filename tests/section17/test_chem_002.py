from batch002_helpers import Batch002Base, attach_fixture_tests, q, date
from copy import deepcopy
from fractions import Fraction

@attach_fixture_tests
class CHEM002Tests(Batch002Base):
    task="BIE-EVAL-CHEM-002"

    def test_step_coefficients_scale_net_not_classification(self):
        d=self.input();v=self.values(d)
        for step in d['steps']:
            for side in ('reactants','products'):step[side]={k:3*n for k,n in step[side].items()}
        w=self.values(d);self.assertEqual({k:3*n for k,n in v['net_reactants'].items()},w['net_reactants']);self.assertEqual(v['intermediates'],w['intermediates']);self.assertFalse(w['mechanism_experimentally_established'])
    def test_identical_left_right_has_no_net_reaction(self):
        d={'op':'audit_steps','species':[{'id':'A','formula':'H2','charge':0}],'steps':[{'reactants':{'A':1},'products':{'A':1}}]};self.rejected(d,'NO_NET_REACTION')
    def test_charge_not_only_atoms_conserved(self):
        d={'op':'audit_steps','species':[{'id':'A','formula':'H','charge':1},{'id':'B','formula':'H','charge':0}],'steps':[{'reactants':{'A':1},'products':{'B':1}}]};self.rejected(d,'UNBALANCED_ELEMENTARY_STEP')
    def test_unknown_species_not_silently_dropped(self):
        d=self.input();d['steps'][0]['reactants']['ghost']=1;self.rejected(d,'UNKNOWN_SPECIES')
    def test_zero_coefficient_refused(self):
        d=self.input();d['steps'][0]['reactants'][next(iter(d['steps'][0]['reactants']))]=0;self.rejected(d,'INVALID_INTEGER')
    def test_integer_one_is_not_elementary_attestation(self):self.rejected({'op':'elementary_rate_law','reactants':{'A':1},'is_elementary':1},'ELEMENTARY_STEP_REQUIRED')
    def test_unsupported_high_molecularity_refused(self):self.rejected({'op':'elementary_rate_law','reactants':{'A':3,'B':1},'is_elementary':True},'MOLECULARITY_OUTSIDE_PROFILE')
    def test_energy_zero_shift_preserves_barriers(self):
        d={'op':'energy_profile','energies_kJ_per_mol':[-5,40,10,65,0]};v=self.values(d);d['energies_kJ_per_mol']=[n+200 for n in d['energies_kJ_per_mol']];self.assertEqual(v,self.values(d));self.assertFalse(v['rate_determining_step_inferred'])
    def test_reversed_path_exchanges_forward_reverse(self):
        d={'op':'energy_profile','energies_kJ_per_mol':[0,50,-10,30,-20]};v=self.values(d);d['energies_kJ_per_mol'].reverse();w=self.values(d);self.assertEqual(v['forward_barriers_kJ_per_mol'][::-1],w['reverse_barriers_kJ_per_mol']);self.assertEqual(Fraction(v['net_energy_change_kJ_per_mol']),-Fraction(w['net_energy_change_kJ_per_mol']))
    def test_even_energy_sequence_refused(self):self.rejected({'op':'energy_profile','energies_kJ_per_mol':[0,40,10,50]},'ALTERNATING_MINIMA_MAXIMA_REQUIRED')
