from copy import deepcopy
import json,random,unittest
from bie.compiler.frame_runtime_contract import plan_frame_runtime,CompilerQAError
from bie.compiler.frame_state_consumer import runtime_at,emit_runtime
from bie.compiler.hardened_scene_compile import compile_h3_scene
from tests.compiler.h6_test_support import *

class StateConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=state_scene();cls.r=compile_h3_scene(cls.p,target=BIG);cls.plan=plan_frame_runtime(cls.r.effective_document,BIG);cls.data=execute(cls.r)
    def test_source_gate_real_parser(self):self.assertTrue(self.r.receipt.source_gate_passed);self.assertEqual(self.r.receipt.parser_status,'PASS')
    def test_every_frame_python_js_parity(self):
        for row in self.data['trees']:
            with self.subTest(frame=row['frame']):self.assertEqual(row['state'],runtime_at(self.plan,row['frame']))
    def test_reverse_and_repeated_frames_do_not_depend_on_history(self):
        frames=list(range(47,-1,-1))+[0,30,0,30,12];d=execute(self.r,frames)
        self.assertEqual([r['state'] for r in d['trees']],[runtime_at(self.plan,f) for f in frames])
    def test_exact_change_boundary(self):
        self.assertNotEqual(runtime_at(self.plan,11)['state'],runtime_at(self.plan,12)['state']);self.assertEqual(runtime_at(self.plan,12)['applied_event_ids'],['step1'])
    def test_late_event_boundary(self):self.assertEqual(runtime_at(self.plan,30)['applied_event_ids'],['step1','step2'])
    def test_illegal_frame_fails(self):
        for f in [-1,48,False,1.5]:
            with self.subTest(f=f), self.assertRaises(CompilerQAError):runtime_at(self.plan,f)
    def test_no_effect_or_mutable_cursor(self):
        s=emit_runtime(self.plan).content
        for bad in ['useEffect','useState','setTimeout','Date.now','Math.random','eval(']:self.assertNotIn(bad,s)
    def test_literal_multilingual_contents_emitted(self):
        s=str(self.data['trees'][30]['tree']);self.assertIn('اردو',s);self.assertIn('INITIAL {2+2}',s);self.assertNotIn('not markup\', \'props',s)
    def test_text_not_duplicated_by_initial_children(self):
        tree=self.data['trees'][30]['tree'];self.assertNotIn(self.p['elements'][0]['props']['text'],str(tree));self.assertIn('समझें',str(tree))
    def test_runtime_source_is_bound_to_declared_plan(self):
        x=next(f for f in self.r.codegen.files if f.path=='src/bie-frame-runtime-plan.json');self.assertEqual(json.loads(x.content)['plan_sha256'],self.plan['plan_sha256'])
    def test_opacity_and_visibility_change_actual_styles(self):
        for prop,initial,value in [('opacity',1,.25),('visible',True,False)]:
            p=state_scene();p['state_bindings'][0]['property_name']=prop;p['metadata']['compiler_h6']['initial_state']['lesson.phase']=initial
            p['events']=[p['events'][0]];p['events'][0]['payload']['value']=value
            r=compile_h3_scene(p,target=BIG);d=execute(r,[0,12])
            style=[next(n['props']['style'] for n in nodes(row['tree']) if n.get('props',{}).get('data-bie-runtime-target')=='e0') for row in d['trees']]
            self.assertNotEqual(style[0],style[1]);self.assertEqual(style[1]['opacity' if prop=='opacity' else 'visibility'],value if prop=='opacity' else 'hidden')
    def test_clamp_is_explicit(self):
        p=state_scene();b=p['state_bindings'][0];b.update(property_name='opacity',transform='clamp01');p['metadata']['compiler_h6']['initial_state']['lesson.phase']=2;p['events']=[]
        plan=plan_frame_runtime(p,BIG);self.assertEqual(runtime_at(plan,0)['targets']['e0']['opacity'],1)
    def test_unknown_boolean_coercion_blocked(self):
        p=state_scene();p['state_bindings'][0]['property_name']='visible'
        with self.assertRaisesRegex(CompilerQAError,'TYPE'):plan_frame_runtime(p,BIG)
    def test_generated_props_are_safe_data(self):
        self.assertIn('bound.text as string',next(f.content for f in self.r.codegen.files if 'runtime-layers' in f.path));self.assertFalse(self.data['accepted'])
    def test_changed_fps_not_silently_replayed(self):
        with self.assertRaisesRegex(AssertionError,'FPS_MISMATCH'):execute(self.r,[0],replace(BIG,fps=30))
    def test_state_snapshots_are_independent(self):
        s=runtime_at(self.plan,12);s['state']['lesson.phase']='mutated';self.assertNotEqual(runtime_at(self.plan,12)['state']['lesson.phase'],'mutated')
    def test_reflow_style_kept(self):
        from bie.compiler.frame_state_consumer import text_style
        e=deepcopy(self.p['elements'][0]);e['props']['compiler_layout']={'font_px':24,'line_height':1.4,'padding_px':8}
        style=text_style(e);self.assertEqual(style['fontSize'],24);self.assertEqual(style['padding'],8);self.assertEqual(style['lineHeight'],1.4)
    def test_state_source_has_provenance(self):self.assertTrue(all(x['source_refs'] and x['reasoning_refs'] for x in self.plan['events']))

if __name__=='__main__':unittest.main()
