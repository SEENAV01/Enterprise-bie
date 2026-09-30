from batch002_helpers import Batch002Base, attach_fixture_tests, q, date
from copy import deepcopy
from fractions import Fraction

@attach_fixture_tests
class BIO002Tests(Batch002Base):
    task="BIE-EVAL-BIO-002"

    def test_parent_swap_preserves_cross(self):
        for c in self.cases()[:4]:
            d=deepcopy(c.inputs);v=self.values(d)
            for locus in d['loci']:locus['parent_a'],locus['parent_b']=locus['parent_b'],locus['parent_a']
            self.assertEqual(v,self.values(d))
    def test_four_loci_cartesian_distribution(self):
        d={'op':'mendelian_cross','assortment':'independent','dominance':'complete','loci':[{'gene':g,'parent_a':g+g.lower(),'parent_b':g+g.lower()} for g in 'ABCD']}
        v=self.values(d);self.assertEqual(81,len(v['genotype_probabilities']));self.assertEqual(16,len(v['phenotype_probabilities']));self.assertEqual(Fraction(1,256),Fraction(v['genotype_probabilities']['aabbccdd']));self.assertEqual(1,sum(map(Fraction,v['genotype_probabilities'].values())))
        d['loci'].reverse();self.assertEqual(v,self.values(d))
    def test_five_loci_refused(self):
        d=self.input();d['loci']=[{'gene':g,'parent_a':g+g,'parent_b':g.lower()*2} for g in 'ABCDE'];self.rejected(d,'COLLECTION_SIZE_OR_TYPE')
    def test_duplicate_loci_refused(self):
        d=self.input();d['loci']*=2;self.rejected(d,'DUPLICATE_LOCUS')
    def test_incomplete_dominance_not_silently_assumed(self):
        d=self.input();d['dominance']='incomplete';self.rejected(d,'UNSUPPORTED_ENUM')
    def test_hardy_weinberg_allele_symmetry(self):
        d=self.input(4);d['p']='2/7';v=self.values(d);d['p']='5/7';w=self.values(d)
        self.assertEqual(v['genotype_probabilities']['AA'],w['genotype_probabilities']['aa']);self.assertEqual(v['genotype_probabilities']['Aa'],w['genotype_probabilities']['Aa'])
    def test_hardy_weinberg_mixed_assumption_types(self):
        d=self.input(4);d['assumptions'][0]=True;self.rejected(d,'HARDY_WEINBERG_ASSUMPTIONS_REQUIRED')
    def test_observed_counts_not_equilibrium_inference(self):
        v=self.values({'op':'allele_frequency','AA':0,'Aa':100,'aa':0});self.assertEqual('1/2',v['p']);self.assertFalse(v['equilibrium_established'])
    def test_empty_population_refused(self):self.rejected({'op':'allele_frequency','AA':0,'Aa':0,'aa':0},'EMPTY_POPULATION')
    def test_negative_population_refused(self):self.rejected({'op':'allele_frequency','AA':-1,'Aa':1,'aa':1},'INVALID_INTEGER')
