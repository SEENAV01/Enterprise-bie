from copy import deepcopy
import unittest
from bie.compiler.specialized_equation import compile_specialized_equation
from bie.compiler.specialized_motion import specialized_contract,equation_state
from tests.compiler.h5_test_support import equation_scene,runtime,nodes

class EquationStepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=equation_scene();cls.t=cls.p['tracks'][0];cls.e=cls.p['elements'][0];cls.c=specialized_contract(cls.t)
        cls.result=compile_specialized_equation(cls.t,cls.e)
        cls.frames=(0,12,20,24,36,43,47,60)
        cls.execution=runtime(cls.result,frames=cls.frames,calls=[{'name':'evaluateEquationSteps','args':[f,24]} for f in cls.frames])
    def test_reference_matches_generated_js(self):
        for f,s in zip(self.frames,self.execution['calls']):
            r=equation_state(self.c,f,24);self.assertEqual((s['lower'],s['upper']),(r['lower'],r['upper']))
            self.assertAlmostEqual(s['upperOpacity'],r['upper_opacity'],12)
    def test_first_equation_visible(self):self.assertIn('2(x+1)=6',str(self.execution['trees'][0]['tree']))
    def test_last_equation_visible(self):self.assertIn('x=2',str(self.execution['trees'][-1]['tree']))
    def test_intermediate_pure_state(self):self.assertEqual(equation_state(self.c,24,24),{'lower':1,'upper':2,'upper_opacity':0.,'lower_opacity':1.})
    def test_crossfade_not_metadata_only(self):self.assertGreater(equation_state(self.c,20,24)['upper_opacity'],0)
    def test_alpha_conserves_total(self):
        for f in range(72):
            s=equation_state(self.c,f,24);self.assertAlmostEqual(s['upper_opacity']+s['lower_opacity'],1)
    def test_actual_typeset_svg_nodes(self):self.assertTrue(any(n.get('tag')=='svg' for n in nodes(self.execution['trees'][0]['tree'])))
    def test_side_conditions_survive_every_frame(self):
        for row in self.execution['trees']:self.assertIn('x is real',str(row['tree']))
    def test_mode_honest(self):self.assertIn('typeset-state-crossfade',self.result.source_text);self.assertNotIn('symbol-proof',self.result.source_text)
    def test_declared_alt_each_state(self):
        tree=self.execution['trees'][-1]['tree'];self.assertIn('Equation step 3',tree['props']['aria-label'])
    def test_typesetter_called_for_each_state(self):
        from bie.compiler.equation_typesetting import typeset_latex
        calls=[]
        def render(expr,**kwargs):calls.append(expr);return typeset_latex(expr,**kwargs)
        compile_specialized_equation(self.t,self.e,typesetter=render)
        self.assertEqual(calls,[s['expression'] for s in self.t['parameters']['states']])
    def test_unique_typesetter_ids(self):
        from bie.compiler.equation_typesetting import typeset_latex
        ids=[]
        def render(expr,**kwargs):ids.append(kwargs['element_id']);return typeset_latex(expr,**kwargs)
        compile_specialized_equation(self.t,self.e,typesetter=render);self.assertEqual(len(set(ids)),3)
    def test_source_deterministic(self):self.assertEqual(self.result,compile_specialized_equation(self.t,self.e))
    def test_initial_mismatch_rejected_by_emitter(self):
        e=deepcopy(self.e);e['props']['expression']='replacement'
        with self.assertRaisesRegex(ValueError,'INITIAL_STATE'):compile_specialized_equation(self.t,e)
    def test_no_raw_math_fallback(self):
        t=deepcopy(self.t);t['parameters']['states'][-1]['expression']=r'\unsupportedcommand{x}'
        with self.assertRaises(ValueError):compile_specialized_equation(t,self.e)
    def test_plain_format_not_reinterpreted(self):
        e=deepcopy(self.e);e['props']['format']='plain'
        with self.assertRaisesRegex(ValueError,'TARGET_UNSUPPORTED'):compile_specialized_equation(self.t,e)
    def test_unknown_equation_property_not_discarded(self):
        e=deepcopy(self.e);e['props']['untaught_condition']=True
        with self.assertRaisesRegex(ValueError,'UNCONSUMED'):compile_specialized_equation(self.t,e)
    def test_alt_text_cannot_execute_js(self):
        t=deepcopy(self.t);t['parameters']['states'][0]['alt']='Literal {globalThis.PWNED=true} <tag>'
        r=runtime(compile_specialized_equation(t,self.e),frames=(0,))
        self.assertEqual(r['trees'][0]['tree']['props']['aria-label'],'Literal {globalThis.PWNED=true} <tag>')
    def test_renderer_change_rejected(self):
        e=deepcopy(self.e);e['props']['renderer']='katex'
        with self.assertRaisesRegex(ValueError,'RENDERER_UNSUPPORTED'):compile_specialized_equation(self.t,e)
    def test_evidence_does_not_claim_real_react(self):self.assertIn('TEST_DOUBLES',self.execution['execution_kind']);self.assertFalse(self.result.accepted)

if __name__=='__main__':unittest.main()
