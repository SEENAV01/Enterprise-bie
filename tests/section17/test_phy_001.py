from copy import deepcopy
import math
from domain_helpers import DomainBase, q, vec
from bie.evaluation.benchmarks.domains.coulomb import solve

class CoulombTests(DomainBase):
    def data(self):
        return {'op':'force_on_charge','charges':[{'q':q(1,'uC'),'position':vec((0,0,0),'m')},{'q':q(1,'uC'),'position':vec((1,0,0),'m')}],'target_index':1,'k_N_m2_per_C2':9e9}
    def test_authored_reference_pack(self): self.replay_pack('BIE-EVAL-PHY-001')
    def test_independent_inverse_square(self):
        a=self.data(); b=deepcopy(a);b['charges'][1]['position']=vec((3,0,0),'m')
        self.assertAlmostEqual(solve(a)['magnitude_N']/9,solve(b)['magnitude_N'])
    def test_charge_product_scaling(self):
        a=self.data();b=deepcopy(a);b['charges'][0]['q']=q(4,'uC');b['charges'][1]['q']=q(3,'uC')
        self.assertAlmostEqual(solve(a)['magnitude_N']*12,solve(b)['magnitude_N'])
    def test_newton_pair_action_reaction(self):
        a=self.data();f=solve(a)['force_N'];a['target_index']=0
        for x,y in zip(f,solve(a)['force_N']):self.assertAlmostEqual(x,-y)
    def test_translation_invariance(self):
        a=self.data();f=solve(a);a['charges'][0]['position']=vec((4,8,16),'m');a['charges'][1]['position']=vec((5,8,16),'m')
        self.assertEqual(f,solve(a))
    def test_rotation_covariance(self):
        a=self.data();a['charges'][1]['position']=vec((0,1,0),'m');self.assertEqual([0,.009,0],solve(a)['force_N'])
    def test_unit_conversion_equivalence(self):
        a=self.data();f=solve(a);a['charges'][0]['q']=q(1000,'nC');a['charges'][1]['position']=vec((100,0,0),'cm')
        for x,y in zip(f['force_N'],solve(a)['force_N']):self.assertAlmostEqual(x,y)
    def test_superposition_cancels(self):
        a=self.data();a['charges'].append({'q':q(1,'uC'),'position':vec((2,0,0),'m')});self.assertEqual(0,solve(a)['magnitude_N'])
    def test_negative_charge_attracts(self):
        a=self.data();a['charges'][0]['q']=q(-1,'uC');self.assertLess(solve(a)['force_N'][0],0)
    def test_zero_test_charge(self):
        a=self.data();a['charges'][1]['q']=q(0,'C');self.assertEqual(0,solve(a)['magnitude_N'])
    def test_bad_distance_unit(self):
        a=self.data();a['charges'][0]['position']['unit']='kg';self.code('UNIT_DIMENSION_MISMATCH',solve,a)
    def test_boolean_charge_rejected(self):
        a=self.data();a['charges'][0]['q']['value']=True;self.code('INVALID_NUMBER',solve,a)
    def test_boolean_target_rejected(self):
        a=self.data();a['target_index']=True;self.code('INVALID_INTEGER',solve,a)
    def test_nan_rejected(self):
        a=self.data();a['charges'][0]['q']['value']=float('nan');self.code('NONFINITE_OR_OUT_OF_RANGE',solve,a)
    def test_coincidence_rejected(self):
        a=self.data();a['charges'][1]['position']=vec((0,0,0),'m');self.code('COINCIDENT_OR_UNRESOLVED_POINT_CHARGES',solve,a)
    def test_constant_must_be_positive(self):
        a=self.data();a['k_N_m2_per_C2']=0;self.code('NONPOSITIVE_COULOMB_CONSTANT',solve,a)
    def test_three_dimensional_vectors_required(self):
        a=self.data();a['charges'][1]['position']=vec((1,0),'m');self.code('VECTOR_DIMENSION_MISMATCH',solve,a)
    def test_unsupported_medium_not_silently_ignored(self):
        a=self.data();a['relative_permittivity']=80;self.code('INVALID_FIELDS',solve,a)
    def test_wrong_force_direction_seed_rejected(self): self.mutant('BIE-EVAL-PHY-001',0,['values','force_N',0],-.009)
    def test_wrong_inverse_square_seed_rejected(self): self.mutant('BIE-EVAL-PHY-001',2,['values','magnitude_N'],.3)
