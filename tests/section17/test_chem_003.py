from batch002_helpers import Batch002Base, attach_fixture_tests, q, date
from copy import deepcopy
from fractions import Fraction

@attach_fixture_tests
class CHEM003Tests(Batch002Base):
    task="BIE-EVAL-CHEM-003"

    def test_nested_formula_parser(self):
        from bie.evaluation.benchmarks.domains.chemistry_common import parse_formula
        self.assertEqual({'K':4,'N':2,'O':14,'S':4},parse_formula('K4[ON(SO3)2]2'))
    def test_formula_invalid_syntax_and_resource_bounds(self):
        from bie.evaluation.benchmarks.domains.chemistry_common import parse_formula
        from bie.evaluation.benchmarks.models import BenchmarkError
        for formula in ['Xx','2H2O','H0','H01','(H2]','()','H2O(aq)','[13C]','H10001','(((((H)))))','H2O.' ]:
            with self.subTest(formula=formula),self.assertRaises(BenchmarkError):parse_formula(formula)
    def test_formula_grouped_and_expanded_equivalent(self):
        from bie.evaluation.benchmarks.domains.chemistry_common import parse_formula
        for n in range(1,20):self.assertEqual(parse_formula(f'(CH2){n}'),parse_formula(f'C{n}H{2*n}'))
    def test_balance_input_order_does_not_change_answer(self):
        d=self.input(1);v=self.values(d);d['reactants'].reverse();d['products'].reverse();self.assertEqual(v,self.values(d))
    def test_primitive_coefficients_known_carbon_example(self):
        def s(i,f):return {'id':i,'formula':f,'charge':0}
        d={'op':'balance','reactants':[s('C','C'),s('O','O2')],'products':[s('CO','CO')]};v=self.values(d);self.assertEqual({'C':2,'O':1},v['reactants']);self.assertEqual({'CO':2},v['products'])
    def test_extent_coefficient_scaling_preserves_production(self):
        d=self.input(3);v=self.values(d);d['coefficients']={k:2*n for k,n in d['coefficients'].items()};w=self.values(d);self.assertEqual(v['produced_mol'],w['produced_mol']);self.assertEqual(Fraction(v['extent_mol'])/2,Fraction(w['extent_mol']))
    def test_missing_feed_not_treated_as_unlimited(self):
        d=self.input(3);d['feed_mol'].pop(next(iter(d['feed_mol'])));self.rejected(d,'COMPLETE_REACTANT_FEED_REQUIRED')
    def test_extra_feed_not_cherry_picked(self):
        d=self.input(3);d['feed_mol']['ghost']=1;self.rejected(d,'COMPLETE_REACTANT_FEED_REQUIRED')
    def test_duplicate_species_ids_not_merged(self):
        d=self.input();d['products'][0]['id']=d['reactants'][0]['id'];self.rejected(d,'DUPLICATE_SPECIES')
    def test_zero_theoretical_yield_rejected(self):self.rejected({'op':'percent_yield','actual_mol':0,'theoretical_mol':0},'QUANTITY_OUT_OF_PROFILE')
