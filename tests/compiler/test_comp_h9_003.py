import unittest
from copy import deepcopy
from bie.compiler.highlight_compiler import *
from bie.compiler.hardened_scene_compile import compile_h3_scene
from tests.compiler.h9_test_support import highlight_scene,T,runtime,nodes,full_tree

class HighlightConsumerTests(unittest.TestCase):
    def emit(self,p):return compile_highlight_element(p['elements'][-1],scene=p,target=T)
    def bad(self,p,code):
        with self.assertRaisesRegex(ValueError,code):self.emit(p)
    def test_all_four_modes_emit_visible_geometry(self):
        for mode in ('outline','fill','spotlight','underline'):
            p=highlight_scene(mode);r=self.emit(p);out=runtime(r,frames=[0],fps=T.fps);tags=[n['tag'] for n in nodes(out['trees'][0]['tree'])];self.assertIn('line' if mode=='underline' else 'polygon',tags)
    def test_no_context_no_fake_highlight(self):
        p=highlight_scene();self.assertRaisesRegex(ValueError,'CONTEXT_REQUIRED',compile_highlight_element,p['elements'][-1])
    def test_target_geometry_not_guessed(self):
        p=highlight_scene();g=highlight_geometry(p['elements'][-1],p,T);self.assertAlmostEqual(g['frames'][0][0]['points'][0][0],136);self.assertAlmostEqual(g['frames'][0][0]['points'][0][1],112.5)
    def test_follows_translated_target_every_frame(self):
        p=highlight_scene(moving=True);g=highlight_geometry(p['elements'][-1],p,T);self.assertEqual(len(g['frames']),12);self.assertAlmostEqual(g['frames'][-1][0]['points'][0][0]-g['frames'][0][0]['points'][0][0],50)
    def test_source_target_ids_preserved(self):
        p=highlight_scene();self.assertIn('"target_id": "e0"',self.emit(p).source_text)
    def test_reverse_seek_no_stateful_drift(self):
        p=highlight_scene(moving=True);r=self.emit(p);a=runtime(r,frames=[0,11,5,0],fps=T.fps);self.assertEqual(a['trees'][0]['tree'],a['trees'][-1]['tree'])
    def test_self_reference_rejected(self):
        p=highlight_scene();p['elements'][-1]['props']['target_element_ids']=['h'];self.bad(p,'TARGET_INVALID')
    def test_missing_target(self):
        p=highlight_scene();p['elements'][-1]['props']['target_element_ids']=['missing'];self.bad(p,'TARGET_MISSING')
    def test_duplicate_target(self):
        p=highlight_scene();p['elements'][-1]['props']['target_element_ids']=['e0','e0'];self.bad(p,'TARGET_INVALID')
    def test_unbound_target_provenance(self):
        p=highlight_scene();p['elements'][0]['source_refs'].append('new');self.bad(p,'PROVENANCE_UNBOUND')
    def test_source_context_cannot_be_substituted(self):
        p=highlight_scene();h=deepcopy(p['elements'][-1]);h['props']['mode']='fill';self.assertRaisesRegex(ValueError,'CONTEXT_MISMATCH',compile_highlight_element,h,scene=p,target=T)
    def test_target_outside_highlight_frame_rejected(self):
        p=highlight_scene();p['elements'][-1]['normalized_box']['width']=.1;self.bad(p,'OUTSIDE')
    def test_unknown_parameter(self):
        p=highlight_scene();p['elements'][-1]['props']['target_selector']='#secret';self.bad(p,'FIELDS')
    def test_extra_opacity_not_silently_ignored(self):
        p=highlight_scene();p['elements'][-1]['props']['fill_opacity']=.2;self.bad(p,'UNCONSUMED')
    def test_checked_scene_declared_overlap(self):
        p=highlight_scene(moving=True);r=compile_h3_scene(p,target=T);self.assertTrue(r.receipt.source_gate_passed,r.receipt.findings)
    def test_undeclared_overlay_blocks_source_gate(self):
        p=highlight_scene();p['metadata'].pop('compiler_h3');r=compile_h3_scene(p,target=T);self.assertFalse(r.receipt.source_gate_passed);self.assertIn('LAYOUT_UNDECLARED_OVERLAP',[f.code for f in r.receipt.findings])
    def test_full_scene_contains_target_and_highlight(self):
        p=highlight_scene();r=compile_h3_scene(p,target=T);tree=full_tree(r,frames=[0],target=T)['trees'][0]['tree'];s=str(tree);self.assertIn('Source-bound highlight',s);self.assertIn('data-bie-highlight-target',s)
    def test_budget_not_sampled(self):
        p=highlight_scene();p['duration_ms']=1100000;self.bad(p,'FRAME_BUDGET')
    def test_other_highlight_cannot_be_target(self):
        p=highlight_scene();p['elements'][0]['element_type']='highlight';self.bad(p,'TARGET_MISSING')
    def test_reproducible(self):
        p=highlight_scene();self.assertEqual(self.emit(p),self.emit(p))
