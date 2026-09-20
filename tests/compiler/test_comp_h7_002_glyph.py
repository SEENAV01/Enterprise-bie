from copy import deepcopy
from pathlib import Path
import unittest
from bie.compiler.glyph_motion import *
from bie.compiler.specialized_motion import specialized_contract
from bie.compiler.specialized_equation import compile_specialized_equation
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.equation_typesetting import typeset_latex
from tests.compiler.h7_test_support import glyph_scene,reduced,BIG
from tests.compiler.h5_test_support import full_tree,nodes

class GlyphCorrespondenceTests(unittest.TestCase):
    def setUp(self):
        self.p=glyph_scene();self.t=self.p['tracks'][0];self.layouts=[typeset_latex(s['expression'],element_id='test'+str(i)) for i,s in enumerate(self.t['parameters']['states'])]
    def test_source_compiles(self):r=compile_h3_scene(self.p,target=BIG);self.assertTrue(r.receipt.source_gate_passed,r.receipt)
    def test_actual_shapes_have_affine_placements(self):
        a=flatten_layout(self.layouts[0]);self.assertTrue(len(a)>1);self.assertTrue(all(len(x['matrix'])==6 for x in a));self.assertTrue(all(x['shape']['d'] for x in a))
    def test_complete_glyph_sets_preserved(self):
        p=glyph_layout_plan(self.layouts,self.t['parameters']['glyph_pairs']);self.assertEqual([len(x) for x in p['states']],[len(flatten_layout(l)) for l in self.layouts])
    def test_equal_outline_pairs_only(self):
        p=glyph_layout_plan(self.layouts,self.t['parameters']['glyph_pairs']);self.assertTrue(all(p['states'][i][a]['shape_sha256']==p['states'][i+1][b]['shape_sha256'] for i,rows in enumerate(p['pairs']) for a,b in rows))
    def test_no_symbolic_equivalence_claim(self):p=glyph_layout_plan(self.layouts,self.t['parameters']['glyph_pairs']);self.assertEqual(p['semantic_equivalence'],'NOT_VERIFIED');self.assertFalse(p['accepted'])
    def test_mismatched_outline_rejected(self):
        pairs=deepcopy(self.t['parameters']['glyph_pairs']);pairs[0]=[[0,0]];self.assertRaisesRegex(ValueError,'OUTLINE_MISMATCH',glyph_layout_plan,self.layouts,pairs)
    def test_duplicate_source_rejected(self):
        pairs=deepcopy(self.t['parameters']['glyph_pairs']);pairs[0]*=2;self.assertRaisesRegex(ValueError,'PAIR_INVALID',glyph_layout_plan,self.layouts,pairs)
    def test_missing_transition_rejected(self):self.assertRaisesRegex(ValueError,'COVERAGE',glyph_layout_plan,self.layouts,[])
    def test_negative_index_rejected(self):
        pairs=deepcopy(self.t['parameters']['glyph_pairs']);pairs[0]=[[-1,0]];self.assertRaises(ValueError,glyph_layout_plan,self.layouts,pairs)
    def test_noninteger_index_rejected(self):
        pairs=deepcopy(self.t['parameters']['glyph_pairs']);pairs[0]=[[True,0]];self.assertRaises(ValueError,glyph_layout_plan,self.layouts,pairs)
    def test_unknown_mode_remains_blocked(self):self.t['parameters']['mode']='symbol-matched';self.assertRaises(ValueError,specialized_contract,self.t)
    def test_crossfade_cannot_ignore_pairs(self):self.t['parameters']['mode']='typeset-state-crossfade';self.assertRaises(ValueError,specialized_contract,self.t)
    def test_invalid_transform_rejected(self):self.assertRaisesRegex(ValueError,'UNSUPPORTED',transform,'rotate(10)')
    def test_affine_composition(self):self.assertEqual(transform('translate(10 20) scale(2 -2)'),[2.,0.,0.,-2.,10.,20.])
    def test_nonfinite_transform_reject(self):self.assertRaises(ValueError,transform,'translate(inf 0)')
    def test_undefined_local_glyph_reject(self):
        l={'tree':{'tag':'svg','attrs':{},'children':[{'tag':'use','attrs':{'href':'#missing'},'children':[]}]}};self.assertRaisesRegex(ValueError,'REFERENCE',flatten_layout,l)
    def test_reduced_milestones_compile(self):r=compile_h3_scene(reduced(self.p),target=BIG,motion_preference='reduced');self.assertTrue(r.receipt.source_gate_passed)
    def test_actual_javascript_paths_move(self):
        r=compile_h3_scene(self.p,target=BIG);data=full_tree(r,frames=[0,20,23,47]);trees=[row['tree'] for row in data['trees']]
        paths=[[n for n in nodes(tree) if n.get('tag')=='path' and n.get('props',{}).get('data-bie-glyph-kind')=='matched'] for tree in trees]
        # Runtime bridge JSON shape is asserted in test, not a real Remotion result.
        self.assertTrue(paths[0]);self.assertNotEqual([n['props']['transform'] for n in paths[0]],[n['props']['transform'] for n in paths[1]])
    def test_side_conditions_preserved(self):r=compile_specialized_equation(self.t,self.p['elements'][0]);self.assertIn('sideConditions',r.source_text);self.assertIn('glyph-matched-affine',r.source_text)
