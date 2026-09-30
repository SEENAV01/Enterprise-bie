import math
from domain_helpers import DomainBase, q
from bie.evaluation.benchmarks.domains.waves import solve

class WavesTests(DomainBase):
    def traveling(self):return dict(op='traveling_wave_sample',amplitude=q(.5,'m'),wavelength=q(4,'m'),frequency=q(2,'Hz'),position=q(0,'m'),time=q(0,'s'),phase=q(0,'rad'),direction='POSITIVE_X')
    def test_authored_reference_pack(self):self.replay_pack('BIE-EVAL-PHY-003')
    def test_dispersion_identity(self):
        r=solve(dict(op='wave_properties',wavelength=q(4,'m'),frequency=q(2,'Hz')));self.assertAlmostEqual(r['phase_speed_mps'],r['omega_radps']/r['k_radpm'])
    def test_wave_units(self):
        r=solve(dict(op='wave_properties',wavelength=q(400,'cm'),frequency=q(.002,'kHz')));self.assertEqual(8,r['phase_speed_mps'])
    def test_particle_not_phase_speed(self):
        r=solve(self.traveling());self.assertAlmostEqual(-2*math.pi,r['particle_velocity_mps']);self.assertEqual(8,r['phase_velocity_mps'])
    def test_direction_reverses_particle_velocity_at_origin(self):
        d=self.traveling();a=solve(d);d['direction']='NEGATIVE_X';b=solve(d);self.assertEqual(-a['particle_velocity_mps'],b['particle_velocity_mps']);self.assertEqual(-8,b['phase_velocity_mps'])
    def test_periodic_time(self):
        d=self.traveling();a=solve(d);d['time']=q(.5,'s');b=solve(d);self.assertAlmostEqual(a['displacement_m'],b['displacement_m']);self.assertAlmostEqual(a['particle_velocity_mps'],b['particle_velocity_mps'])
    def test_periodic_space(self):
        d=self.traveling();d['position']=q(4,'m');self.assertAlmostEqual(0,solve(d)['displacement_m'])
    def test_zero_amplitude_zero_particle_motion(self):
        d=self.traveling();d['amplitude']=q(0,'m');r=solve(d);self.assertEqual(0,r['particle_velocity_mps']);self.assertEqual(0,r['displacement_m'])
    def test_linear_phase_cancellation(self):
        r=solve(dict(op='linear_superposition',components=[dict(amplitude=q(2,'m'),phase=q(90,'deg')),dict(amplitude=q(2,'m'),phase=q(270,'deg'))]));self.assertAlmostEqual(0,r['displacement_m'])
    def test_linear_amplitude_scaling(self):
        a=dict(op='linear_superposition',components=[dict(amplitude=q(2,'m'),phase=q(90,'deg'))]);r=solve(a);a['components'][0]['amplitude']=q(6,'m');self.assertAlmostEqual(3*r['displacement_m'],solve(a)['displacement_m'])
    def test_fixed_string_fundamental(self):
        r=solve(dict(op='fixed_string_mode',length=q(2,'m'),wave_speed=q(100,'m/s'),mode=1));self.assertEqual({'frequency_Hz':25,'wavelength_m':4,'node_count_including_ends':2},r)
    def test_harmonic_scaling(self):
        r=solve(dict(op='fixed_string_mode',length=q(2,'m'),wave_speed=q(100,'m/s'),mode=5));self.assertEqual(125,r['frequency_Hz']);self.assertEqual(6,r['node_count_including_ends'])
    def test_boolean_mode_rejected(self):self.code('INVALID_INTEGER',solve,dict(op='fixed_string_mode',length=q(2,'m'),wave_speed=q(100,'m/s'),mode=True))
    def test_frequency_dimension(self):self.code('UNIT_DIMENSION_MISMATCH',solve,dict(op='wave_properties',wavelength=q(2,'m'),frequency=q(2,'s')))
    def test_negative_amplitude_rejected(self):
        d=self.traveling();d['amplitude']=q(-1,'m');self.code('NEGATIVE_QUANTITY',solve,d)
    def test_phase_resolution_limit(self):
        d=self.traveling();d['phase']=q(1e9,'rad');self.code('PHASE_RESOLUTION_LIMIT',solve,d)
    def test_direction_validation(self):
        d=self.traveling();d['direction']='UP';self.code('INVALID_DIRECTION',solve,d)
    def test_nonlinear_assumption_not_silently_applied(self):self.code('UNSUPPORTED_OPERATION',solve,{'op':'nonlinear_superposition'})
    def test_phase_particle_confusion_seed_rejected(self):self.mutant('BIE-EVAL-PHY-003',4,['values','particle_velocity_mps'],2)
    def test_node_count_seed_rejected(self):self.mutant('BIE-EVAL-PHY-003',6,['values','node_count_including_ends'],3)
