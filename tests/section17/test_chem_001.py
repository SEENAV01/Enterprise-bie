from batch002_helpers import Batch002Base, attach_fixture_tests, q, date
from copy import deepcopy
from fractions import Fraction

@attach_fixture_tests
class CHEM001Tests(Batch002Base):
    task="BIE-EVAL-CHEM-001"

    def test_formal_charge_consistent_with_total_electrons(self):
        for c in self.cases()[:4]:
            v=self.values(c.inputs);self.assertEqual(sum(v['formal_charges'].values()),v['formal_charge_sum']);self.assertEqual(v['required_valence_electrons']-v['drawn_valence_electrons'],v['formal_charge_sum']-c.inputs['total_charge'])
    def test_all_supported_vsepr_shapes(self):
        rows=[(2,0,'linear','linear'),(3,0,'trigonal_planar','trigonal_planar'),(2,1,'trigonal_planar','bent'),(4,0,'tetrahedral','tetrahedral'),(3,1,'tetrahedral','trigonal_pyramidal'),(2,2,'tetrahedral','bent')]
        for b,l,e,m in rows:
            v=self.values({'op':'vsepr','bonded_domains':b,'lone_pairs':l});self.assertEqual(e,v['electron_geometry']);self.assertEqual(m,v['molecular_geometry'])
    def test_atom_and_bond_order_irrelevant(self):
        d=self.input();a=self.values(d);d['atoms'].reverse();d['bonds'].reverse()
        for b in d['bonds']:b['a'],b['b']=b['b'],b['a']
        self.assertEqual(a,self.values(d))
    def test_self_bond_refused(self):
        d=self.input();d['bonds'][0]['b']=d['bonds'][0]['a'];self.rejected(d,'SELF_BOND')
    def test_reverse_duplicate_bond_refused(self):
        d=self.input();b=deepcopy(d['bonds'][0]);b['a'],b['b']=b['b'],b['a'];d['bonds'].append(b);self.rejected(d,'DUPLICATE_BOND')
    def test_boolean_bond_order_refused(self):
        d=self.input();d['bonds'][0]['order']=True;self.rejected(d,'INVALID_INTEGER')
    def test_oversized_atom_graph_refused(self):
        d=self.input();d['atoms']*=11;self.rejected(d,'COLLECTION_SIZE_OR_TYPE')
    def test_expanded_octet_element_refused(self):
        d=self.input();d['atoms'][0]['element']='P';self.rejected(d,'UNSUPPORTED_ENUM')
    def test_omitted_bonding_claims_are_defects(self):
        v=self.values({'op':'audit_concepts','claims':{}});self.assertFalse(v['consistent']);self.assertEqual(4,len(v['defects']))
    def test_numeric_boolean_claim_not_equivalent(self):
        d=self.input(7);d['claims']['resonance_is_temporal_switching']=0;self.assertFalse(self.values(d)['consistent'])
