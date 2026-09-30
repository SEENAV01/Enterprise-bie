from copy import deepcopy
from domain_helpers import DomainBase, q, vec
from bie.evaluation.benchmarks.domains.mechanics import solve

class MechanicsTests(DomainBase):
    def motion(self): return dict(op='constant_acceleration_1d',x0=q(1,'m'),v0=q(2,'m/s'),a=q(4,'m/s^2'),time=q(3,'s'))
    def collision(self): return dict(op='perfectly_inelastic_1d',mass1=q(2,'kg'),mass2=q(6,'kg'),velocity1=q(8,'m/s'),velocity2=q(-4,'m/s'))
    def test_authored_reference_pack(self): self.replay_pack('BIE-EVAL-PHY-002')
    def test_motion_independent_analytic(self):self.assertEqual({'position_m':25,'velocity_mps':14},solve(self.motion()))
    def test_zero_acceleration_linear(self):
        d=self.motion();d['a']=q(0,'m/s^2');self.assertEqual({'position_m':7,'velocity_mps':2},solve(d))
    def test_coordinate_translation(self):
        a=self.motion();r=solve(a);a['x0']=q(101,'m');s=solve(a);self.assertEqual(r['position_m']+100,s['position_m']);self.assertEqual(r['velocity_mps'],s['velocity_mps'])
    def test_time_unit_conversion(self):
        d=self.motion();r=solve(d);d['time']=q(3000,'ms');self.assertEqual(r,solve(d))
    def test_negative_elapsed_time_rejected(self):
        d=self.motion();d['time']=q(-1,'s');self.code('NEGATIVE_QUANTITY',solve,d)
    def test_force_mass_inverse_scaling(self):
        d=dict(op='net_acceleration',mass=q(2,'kg'),forces=[vec((4,8,12),'N')]);r=solve(d)['acceleration_mps2'];d['mass']=q(4,'kg')
        self.assertEqual([v/2 for v in r],solve(d)['acceleration_mps2'])
    def test_equal_opposite_force_zero(self):
        self.assertEqual([0,0,0],solve(dict(op='net_acceleration',mass=q(2,'kg'),forces=[vec((4,8,12),'N'),vec((-4,-8,-12),'N')]))['acceleration_mps2'])
    def test_mass_not_force_units(self):self.code('UNIT_DIMENSION_MISMATCH',solve,dict(op='net_acceleration',mass=q(2,'N'),forces=[vec((1,0,0),'N')]))
    def test_zero_mass_rejected(self):self.code('NONPOSITIVE_QUANTITY',solve,dict(op='net_acceleration',mass=q(0,'kg'),forces=[vec((1,0,0),'N')]))
    def test_empty_force_list_not_a_measurement(self):self.code('INVALID_FORCE_COUNT',solve,dict(op='net_acceleration',mass=q(2,'kg'),forces=[]))
    def test_collision_momentum_independent(self):
        d=self.collision();r=solve(d);self.assertEqual((2*8+6*(-4))/8,r['final_velocity_mps'])
    def test_inelastic_energy_not_conserved(self):
        r=solve(self.collision());self.assertEqual(108,r['kinetic_energy_lost_J']);self.assertGreater(r['kinetic_energy_lost_J'],0)
    def test_comoving_collision_loses_no_energy(self):
        d=self.collision();d['velocity2']=q(8,'m/s');r=solve(d);self.assertEqual(8,r['final_velocity_mps']);self.assertEqual(0,r['kinetic_energy_lost_J'])
    def test_galilean_collision_velocity(self):
        a=self.collision();r=solve(a);a['velocity1']=q(108,'m/s');a['velocity2']=q(96,'m/s');s=solve(a)
        self.assertEqual(r['final_velocity_mps']+100,s['final_velocity_mps']);self.assertEqual(r['kinetic_energy_lost_J'],s['kinetic_energy_lost_J'])
    def test_signed_work_dot_product(self):self.assertEqual(-6,solve(dict(op='constant_force_work',force=vec((2,4,0),'N'),displacement=vec((3,-3,0),'m')))['work_J'])
    def test_work_perpendicular_not_magnitude_product(self):self.assertEqual(0,solve(dict(op='constant_force_work',force=vec((2,0,0),'N'),displacement=vec((0,3,0),'m')))['work_J'])
    def test_unsupported_relativity_rejected(self):self.code('UNSUPPORTED_OPERATION',solve,{'op':'relativistic_collision'})
    def test_wrong_acceleration_seed_rejected(self):self.mutant('BIE-EVAL-PHY-002',3,['values','acceleration_mps2',0],4)
    def test_wrong_energy_seed_rejected(self):self.mutant('BIE-EVAL-PHY-002',5,['values','kinetic_energy_lost_J'],0)
