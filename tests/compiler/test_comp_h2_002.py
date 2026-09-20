from copy import deepcopy
import math,unittest
from bie.compiler.simulation_models import *
from bie.compiler.simulation_compiler import compile_simulation_element
from bie.compiler.generated_code_regression import probe_typescript_sources
from tests.compiler.h2_test_support import element,sim_props,runtime,nodes,text_nodes

class ExecutableSimulationTests(unittest.TestCase):
    def c(self,kind='acceleration'):return simulation_contract(sim_props(kind))
    def bad(self,change,kind='acceleration',code=None):
        p=sim_props(kind);change(p)
        with self.assertRaisesRegex(ValueError,code or 'SIMULATION|UNCONSUMED'):simulation_contract(p)
    def test_constant_acceleration_analytic_state(self):
        s=evaluate_simulation(self.c(),2);self.assertEqual((s['x'],s['y'],s['vx'],s['vy']),(4,4,2,0))
    def test_acceleration_initial_conditions_exact(self):
        s=evaluate_simulation(self.c(),0);self.assertEqual((s['x'],s['y'],s['vx'],s['vy']),(0,0,2,4))
    def test_oscillator_quarter_period(self):
        s=evaluate_simulation(self.c('oscillator'),.5);self.assertAlmostEqual(s['x'],0,12);self.assertAlmostEqual(s['v'],-math.pi,12)
    def test_oscillator_full_period(self):
        s=evaluate_simulation(self.c('oscillator'),2);self.assertAlmostEqual(s['x'],1,12);self.assertAlmostEqual(s['v'],0,12)
    def test_oscillator_energy_invariant(self):
        c=self.c('oscillator')
        for i in range(101):
            s=evaluate_simulation(c,i/50);self.assertAlmostEqual(s['v']**2+math.pi**2*s['x']**2,math.pi**2,10)
    def test_exponential_decay_matches_closed_form(self):self.assertAlmostEqual(evaluate_simulation(self.c('decay'),2)['n'],10/math.e,12)
    def test_decay_monotonic_nonnegative(self):
        vals=[evaluate_simulation(self.c('decay'),i/50)['n'] for i in range(101)];self.assertTrue(all(a>=b>=0 for a,b in zip(vals,vals[1:])))
    def test_zero_rate_is_constant(self):
        p=sim_props('decay');p['parameters']['rate']=0;c=simulation_contract(p);self.assertEqual(evaluate_simulation(c,2)['n'],10)
    def test_derivative_independent_finite_difference(self):
        c=self.c();t=.7;h=1e-5;a=evaluate_simulation(c,t-h);b=evaluate_simulation(c,t+h);s=evaluate_simulation(c,t)
        self.assertAlmostEqual((b['y']-a['y'])/(2*h),s['vy'],8)
    def test_numerical_rk4_independent_oscillator_reference(self):
        x,v=1.,0.;h=.001;w=math.pi
        for i in range(1000):
            k1=(v,-w*w*x);k2=(v+h*k1[1]/2,-w*w*(x+h*k1[0]/2));k3=(v+h*k2[1]/2,-w*w*(x+h*k2[0]/2));k4=(v+h*k3[1],-w*w*(x+h*k3[0]));x+=h/6*(k1[0]+2*k2[0]+2*k3[0]+k4[0]);v+=h/6*(k1[1]+2*k2[1]+2*k3[1]+k4[1])
        s=evaluate_simulation(self.c('oscillator'),1);self.assertAlmostEqual(x,s['x'],9);self.assertAlmostEqual(v,s['v'],9)
    def test_generated_js_state_matches_python_all_models(self):
        for kind in ('acceleration','oscillator','decay'):
            p=sim_props(kind);c=simulation_contract(p);r=compile_simulation_element(element('simulation',p));times=[0,.125,.7,1.,2.]
            out=runtime(r,calls=[{'name':'evaluateSimulation','args':[t]} for t in times])
            for t,js in zip(times,out['calls']):
                for k,v in evaluate_simulation(c,t).items():self.assertAlmostEqual(v,js[k],9)
    def test_generated_markers_move_between_frames(self):
        r=compile_simulation_element(element('simulation',sim_props()));t=runtime(r,frames=(0,12,24))['trees'];p=[nodes(x['tree'],'circle')[0]['props'] for x in t];self.assertNotEqual((p[0]['cx'],p[0]['cy']),(p[1]['cx'],p[1]['cy']))
    def test_generated_state_not_a_json_dump(self):
        r=compile_simulation_element(element('simulation',sim_props()));self.assertNotIn('JSON.stringify(initialState',r.source_text);self.assertIn('evaluateSimulation(time)',r.source_text)
    def test_sample_order_does_not_change_frame_state(self):
        c=self.c();a=simulation_frame_state(c,12,24);simulation_frame_state(c,1,24);simulation_frame_state(c,40,24);self.assertEqual(a,simulation_frame_state(c,12,24))
    def test_prestart_state_held(self):
        p=sim_props();p['start_ms']=1000;c=simulation_contract(p);self.assertEqual(simulation_frame_state(c,0,24)['t'],0)
    def test_after_end_state_held(self):self.assertEqual(simulation_frame_state(self.c(),1000,24)['t'],2)
    def test_outside_model_interval_rejected(self):
        for t in (-1,2.1):
            with self.assertRaises(ValueError):evaluate_simulation(self.c(),t)
    def test_nonfinite_time_rejected(self):
        with self.assertRaises(ValueError):evaluate_simulation(self.c(),float('nan'))
    def test_unknown_model_ref_rejected(self):self.bad(lambda p:p.update(model_ref='toy'),code='MODEL_UNSUPPORTED')
    def test_unversioned_model_rejected(self):self.bad(lambda p:p.update(model_ref='bie.sim.exponential-decay'),code='MODEL_UNSUPPORTED')
    def test_conceptual_dump_is_not_execution(self):self.bad(lambda p:p.update(execution_class='conceptual'),code='EXECUTION_CLASS')
    def test_receipt_ref_cannot_claim_observed_reality(self):self.bad(lambda p:p.update(receipt_ref='forged:1'),code='OBSERVATION_NOT_VERIFIED')
    def test_verified_observed_label_rejected(self):self.bad(lambda p:p.update(execution_class='verified_observed_execution'),code='OBSERVATION_NOT_VERIFIED')
    def test_wrong_units_rejected(self):self.bad(lambda p:p['units'].update(x='cm'),code='UNITS_MISMATCH')
    def test_missing_units_rejected(self):self.bad(lambda p:p.pop('units'),code='UNITS_MISMATCH')
    def test_extra_initial_state_not_dropped(self):self.bad(lambda p:p['initial_state'].update(z=5),code='SCHEMA_INVALID')
    def test_extra_parameter_not_dropped(self):self.bad(lambda p:p['parameters'].update(drag=.1),code='SCHEMA_INVALID')
    def test_nan_parameters_rejected(self):
        p=sim_props();p['parameters']['ax']=float('nan')
        with self.assertRaises(ValueError):simulation_contract(p)
    def test_boolean_parameter_rejected(self):
        p=sim_props();p['parameters']['ax']=True
        with self.assertRaises(ValueError):simulation_contract(p)
    def test_negative_omega_rejected(self):self.bad(lambda p:p['parameters'].update(omega=-1),'oscillator','PARAMETER_INVALID')
    def test_negative_decay_state_rejected(self):self.bad(lambda p:p['initial_state'].update(n=-1),'decay','PARAMETER_INVALID')
    def test_missing_view_rejected(self):self.bad(lambda p:p.pop('view'),code='VIEW_REQUIRED')
    def test_view_clipping_extrema_rejected(self):self.bad(lambda p:p['view'].update(y_max=1),code='VIEW_CLIPS')
    def test_excessive_trajectory_samples_rejected(self):self.bad(lambda p:p.update(trajectory_samples=5000),code='SAMPLING')
    def test_duration_bool_rejected(self):self.bad(lambda p:p.update(duration_ms=True),code='TIME_CONTRACT')
    def test_frame_requires_integer(self):
        with self.assertRaises(ValueError):simulation_frame_state(self.c(),.5,24)
    def test_assumptions_and_units_visible(self):
        tree=runtime(compile_simulation_element(element('simulation',sim_props())))['trees'][0]['tree'];text=' '.join(text_nodes(tree));self.assertIn('not an observed measurement',text);self.assertIn('m/s',text)
    def test_ast_has_no_dynamic_execution(self):
        r=compile_simulation_element(element('simulation',sim_props()));self.assertEqual(probe_typescript_sources(((r.source_path,r.source_text),)).status,'PASS')
    def test_execution_is_not_acceptance(self):self.assertFalse(self.c().accepted)

if __name__=='__main__':unittest.main()
