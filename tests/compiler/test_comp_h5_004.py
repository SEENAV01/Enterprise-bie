from copy import deepcopy
import unittest,math
from bie.compiler.specialized_trace import compile_specialized_trace
from bie.compiler.specialized_motion import specialized_contract,graph_contract,trace_state
from tests.compiler.h5_test_support import trace_scene,runtime,nodes

class TraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=trace_scene();cls.e=cls.p['elements'][0];cls.t=cls.p['tracks'][0]
        cls.c=specialized_contract(cls.t);cls.g=graph_contract(cls.e)
        cls.result=compile_specialized_trace(cls.t,cls.e);cls.frames=(0,7,12,24,36,47,60)
        cls.execution=runtime(cls.result,frames=cls.frames,calls=[{'name':'evaluateTrace','args':[f,24]} for f in cls.frames])
    def bad(self,edit,code):
        e=deepcopy(self.e);edit(e)
        with self.assertRaisesRegex(ValueError,code):compile_specialized_trace(self.t,e)
    def test_python_js_head_matches(self):
        for f,v in zip(self.frames,self.execution['calls']):
            s=trace_state(self.c,self.g,f,24)
            for a,b in zip(s['head'],v['head']):self.assertAlmostEqual(a,b,10)
            for a,b in zip(s['data'],v['data']):self.assertAlmostEqual(a,b,10)
    def test_zero_dash_visibility(self):self.assertEqual(self.execution['calls'][0]['dashOffset'],1)
    def test_final_dash_visibility(self):self.assertEqual(self.execution['calls'][-1]['dashOffset'],0)
    def test_first_source_point_preserved(self):self.assertEqual(self.execution['calls'][0]['data'],[-2,-1])
    def test_last_source_point_preserved(self):self.assertEqual(self.execution['calls'][-1]['data'],[2,1])
    def test_marker_absent_before_draw(self):self.assertFalse(any(n.get('tag')=='circle' for n in nodes(self.execution['trees'][0]['tree'])))
    def test_marker_moves(self):self.assertNotEqual(self.execution['calls'][1]['head'],self.execution['calls'][-1]['head'])
    def test_other_series_stays_visible(self):
        paths=[n for n in nodes(self.execution['trees'][0]['tree']) if n.get('tag')=='path'];self.assertEqual(len(paths),2)
        other=next(n for n in paths if n['props']['data-bie-series-id']=='reference');self.assertNotIn('strokeDashoffset',other['props'])
    def test_units_and_labels_preserved(self):
        text=str(self.execution['trees'][0]['tree']);self.assertIn('Time [s]',text);self.assertIn('Position [m]',text)
    def test_negative_domain_ticks_visible(self):self.assertIn("'-3'",str(self.execution['trees'][0]['tree']));self.assertIn("'-2'",str(self.execution['trees'][0]['tree']))
    def test_coordinates_projected_by_explicit_domains(self):self.assertEqual(self.g['series'][0]['pixels'][0],[48,134])
    def test_arc_length_is_screen_not_time_claim(self):self.assertIn('screen-arc-length',self.result.source_text)
    def test_constant_source_path_over_frames(self):
        paths=[next(n['props']['d'] for n in nodes(row['tree']) if n.get('props',{}).get('data-bie-series-id')=='signal') for row in self.execution['trees']]
        self.assertEqual(len(set(paths)),1)
    def test_bounded_marker_option(self):
        t=deepcopy(self.t);t['parameters']['head_marker']=False;r=runtime(compile_specialized_trace(t,self.e),frames=(47,))
        self.assertFalse(any(n.get('tag')=='circle' for n in nodes(r['trees'][0]['tree'])))
    def test_outside_domain_rejected(self):self.bad(lambda e:e['props']['series'][0]['points'].append([200,1]),'OUTSIDE_DOMAIN')
    def test_reversed_domain_rejected(self):self.bad(lambda e:e['props'].update(x_domain=[2,-2]),'DOMAIN_INVALID')
    def test_missing_axis_units_rejected(self):self.bad(lambda e:e['props'].pop('x_unit'),'UNCONSUMED')
    def test_extra_coordinate_dimension_rejected(self):self.bad(lambda e:e['props']['series'][0]['points'].append([0,1,2]),'POINTS_INVALID')
    def test_duplicate_series_id_rejected(self):self.bad(lambda e:e['props']['series'][1].update(series_id='signal'),'SERIES_INVALID')
    def test_repeated_point_rejected(self):self.bad(lambda e:e['props']['series'][0]['points'].insert(1,[-2,-1]),'POINTS_UNRESOLVED')
    def test_nonfinite_point_rejected(self):self.bad(lambda e:e['props']['series'][0]['points'].append([float('inf'),1]),'NUMBER_INVALID')
    def test_unknown_series_rejected(self):
        t=deepcopy(self.t);t['parameters']['series_id']='absent'
        with self.assertRaisesRegex(ValueError,'SERIES_MISSING'):compile_specialized_trace(t,self.e)
    def test_deterministic_source(self):self.assertEqual(self.result,compile_specialized_trace(self.t,self.e))
    def test_declared_viewbox_matches_emitted_svg_for_all_series_counts(self):
        for count in (1,2,8):
            e=deepcopy(self.e)
            e['props']['series']=[{**deepcopy(e['props']['series'][0]),'series_id':('signal' if i==0 else 's'+str(i))} for i in range(count)]
            g=graph_contract(e);r=runtime(compile_specialized_trace(self.t,e),frames=(0,))
            svg=next(n for n in nodes(r['trees'][0]['tree']) if n.get('tag')=='svg')
            self.assertEqual([float(x) for x in svg['props']['viewBox'].split()],g['viewbox'])
            self.assertEqual(g['viewbox'][3],244+16*count)
    def test_true_only_technical_evidence(self):self.assertFalse(self.result.accepted);self.assertIn('TEST_DOUBLES',self.execution['execution_kind'])

if __name__=='__main__':unittest.main()
