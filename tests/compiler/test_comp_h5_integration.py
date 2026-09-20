from tests.canonical_layout import canonical_archive_path
from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import json,subprocess,sys,tempfile,unittest
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.frame_layout import iter_frame_layers
from tests.compiler.h5_test_support import *


def combined_scene():
    p=equation_scene();e=p['elements'][0];e['normalized_box']={'x':.55,'y':.2,'width':.4,'height':.3}
    g=trace_scene();g['elements'][0]['element_id']='plot';g['elements'][0]['normalized_box']={'x':.05,'y':.12,'width':.45,'height':.7};g['tracks'][0]['element_id']='plot'
    p['elements']+=g['elements'];p['tracks']+=g['tracks'];p['scene_id']='h5-combined-technical'
    # Intentionally append the camera after content replacement: it must not be swallowed.
    cam=camera_scene()['tracks'][0];cam['parameters']['viewport']={'width':512,'height':216};cam['parameters']['from'].update(focus_x=256,focus_y=108,zoom=.7);cam['parameters']['to'].update(focus_x=256,focus_y=108,zoom=1)
    p['tracks'].append(cam)
    return p

class CrossConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=combined_scene();cls.r=compile_h3_scene(cls.p,target=BIG);cls.trees=full_tree(cls.r)
    def test_combined_passes(self):self.assertTrue(self.r.receipt.source_gate_passed)
    def test_camera_not_swallowed(self):
        for row in self.trees['trees']:self.assertTrue(any(n.get('props',{}).get('data-bie-action')=='camera' for n in nodes(row['tree'])))
    def test_morph_not_swallowed(self):
        self.assertIn('x=2',str(self.trees['trees'][-1]['tree']))
    def test_graph_trace_present(self):self.assertTrue(any(n.get('props',{}).get('data-bie-action')=='trace' for n in nodes(self.trees['trees'][0]['tree'])))
    def test_no_duplicate_visible_initial_equation(self):
        for row in self.trees['trees']:
            roots=[n for n in nodes(row['tree']) if n.get('props',{}).get('role')=='math'];self.assertEqual(len(roots),1)
    def test_camera_order_does_not_drop_content(self):
        p=deepcopy(self.p);p['tracks']=[p['tracks'][-1],*p['tracks'][:-1]];r=compile_h3_scene(p,target=BIG)
        self.assertTrue(r.receipt.source_gate_passed)
        for row in full_tree(r)['trees']:self.assertTrue(any(n.get('props',{}).get('data-bie-action')=='camera' for n in nodes(row['tree'])))
    def test_all_layers_all_frames_covered(self):
        rows=list(iter_frame_layers(self.r.effective_document,BIG));self.assertEqual(len(rows),48);self.assertEqual(sum(map(len,rows)),96)
    def test_inputs_not_mutated(self):
        p=combined_scene();copy=deepcopy(p);compile_h3_scene(p,target=BIG);self.assertEqual(p,copy)
    def test_new_contract_binding_evidence_complete(self):
        d=json.loads(next(f.content for f in self.r.codegen.files if f.path=='src/bie-behavior-contracts.json'));self.assertEqual({v['action'] for v in d['specialized']},{'camera','morph','trace'})
    def test_independent_process_source_repeats(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'scene.json';p.write_text(json.dumps(self.p))
            code="import sys,json;from dataclasses import replace;from bie.compiler.qa_scene_compile import CompilerQATarget;from bie.compiler.hardened_scene_compile import compile_h3_scene;t=replace(CompilerQATarget(),compiler_version='1.3.0-comp-h3',width=1280,height=720);print(compile_h3_scene(json.load(open(sys.argv[1])),target=t).codegen.manifest_sha256)"
            r=subprocess.run([sys.executable,'-c',code,str(p)],cwd=ROOT,capture_output=True,text=True,timeout=40);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),self.r.codegen.manifest_sha256)
    def test_parent_fixture_bytes_unchanged(self):
        d=json.loads((ROOT/'lineage/hardening_h4/ORIGINAL_MEMBER_HASHES.json').read_text())['members']
        for name,value in d.items():
            if name.startswith('fixtures/'):self.assertEqual(sha256((canonical_archive_path(ROOT,name)).read_bytes()).hexdigest(),value,name)
    def test_changed_parent_active_bytes_preserved(self):
        d=json.loads((ROOT/'lineage/hardening_h4/ORIGINAL_MEMBER_HASHES.json').read_text())['members']
        for name,value in d.items():
            if name.startswith(('app/','tests/','scripts/')) and sha256((canonical_archive_path(ROOT,name)).read_bytes()).hexdigest()!=value:
                self.assertEqual(sha256((ROOT/'lineage/hardening_h4/originals'/name).read_bytes()).hexdigest(),value,name)

if __name__=='__main__':unittest.main()
