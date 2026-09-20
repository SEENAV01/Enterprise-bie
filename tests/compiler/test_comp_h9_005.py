import unittest,json,tempfile,subprocess,sys
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from bie.compiler.hardened_scene_compile import compile_h3_scene,publish_h3_scene,require_h3_workspace
from bie.compiler.qa_scene_compile import EMITTERS,native_qa_capabilities
from bie.compiler.consumer_coverage import inspect_consumer_coverage,require_dispatch_coverage
from bie.compiler.registered_actions import ACTIONS
from bie.compiler.capability_fallback_qa import inspect_emitted_semantics
from bie.compiler.scene_ir_loader import load_scene_ir_payload
from tests.compiler.h9_test_support import shape_scene,diagram_scene,highlight_scene,action_scene,T
ROOT=Path(__file__).parents[2]

class H9CompilerAdoptionTests(unittest.TestCase):
    def test_all_18_registered_element_names_dispatched(self):
        r=inspect_consumer_coverage();self.assertEqual(r['registry_elements'],18);self.assertEqual([x for x in r['missing'] if x['kind']=='element'],[])
    def test_all_16_registered_action_names_dispatched(self):
        r=inspect_consumer_coverage();self.assertEqual(r['registry_actions'],16);self.assertEqual(r['missing'],[]);require_dispatch_coverage(r)
    def test_complete_dispatch_is_not_complete_behavior(self):
        r=inspect_consumer_coverage();self.assertTrue(r['dispatch_complete']);self.assertFalse(r['behavior_coverage_complete']);self.assertFalse(r['section_exit_permitted'])
    def test_no_extra_registry_names_invented(self):self.assertEqual(inspect_consumer_coverage()['unregistered_dispatch'],{'elements':[],'actions':[]})
    def test_lowerer_removed_detected(self):
        from bie.compiler import registered_actions
        with patch.object(registered_actions,'ACTIONS',frozenset()):self.assertEqual(len(inspect_consumer_coverage()['missing']),7)
    def test_required_capability_request_consumes_new_action(self):
        p=action_scene('static_focus');p['capability_requests']=[{'capability_id':'comp:text','element_id':'e0','element_type':'text','requested_action':'static_focus','required':True}];self.assertTrue(compile_h3_scene(p,target=T).receipt.source_gate_passed)
    def test_capability_name_does_not_bypass_invalid_parameters(self):
        p=action_scene('static_focus');p['tracks'][0]['parameters']['pose']['zoom']=100;p['capability_requests']=[{'capability_id':'comp:text','element_id':'e0','element_type':'text','requested_action':'static_focus','required':True}];self.assertRaises(ValueError,compile_h3_scene,p,target=T)
    def test_checked_publication_and_revalidation(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'project';receipt=publish_h3_scene(diagram_scene(),out,target=T);self.assertTrue(receipt.source_gate_passed);self.assertTrue(require_h3_workspace(out).source_gate_passed)
    def test_tampered_new_primitive_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'project';publish_h3_scene(shape_scene(),out,target=T);path=next((out/'src/elements').glob('Shape*'));path.write_text(path.read_text()+'\n// tamper\n');self.assertRaisesRegex(ValueError,'TAMPERED',require_h3_workspace,out)
    def test_original_actions_not_rewritten_in_source_identity(self):
        p=action_scene('static_trace');r=compile_h3_scene(p,target=T);self.assertEqual(r.effective_document['tracks'],p['tracks']);self.assertTrue(any(f.path=='src/bie-behavior-contracts.json' and 'static_trace' in f.content for f in r.codegen.files))
    def test_source_maps_bind_new_emitter(self):
        r=compile_h3_scene(shape_scene(),target=T);spans=r.bundle.source_map.spans;self.assertTrue(any('Shape_' in str(s) and 'fixture:h3' in str(s) for s in spans))
    def test_highlight_follows_existing_motion_without_discarding_it(self):
        p=highlight_scene(moving=True);r=compile_h3_scene(p,target=T);self.assertEqual(r.effective_document['tracks'],p['tracks']);self.assertEqual(len(r.bundle.animation_results),1)
    def test_source_inputs_not_mutated(self):
        for p in [shape_scene(),diagram_scene(),highlight_scene(),action_scene('state_snapshots')]:
            q=deepcopy(p);compile_h3_scene(p,target=T);self.assertEqual(p,q)
    def test_new_names_not_just_metadata_stub(self):
        for p in [shape_scene(),diagram_scene(),highlight_scene(),action_scene('state_snapshots')]:
            r=compile_h3_scene(p,target=T);self.assertTrue(r.receipt.source_gate_passed);self.assertFalse(any('BlockedElement_' in f.content or 'BlockedTrack_' in f.content for f in r.codegen.files))
    def test_source_publication_is_not_dependency_installation_or_render(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'p';publish_h3_scene(shape_scene(),out,target=T)
            # Checked source is not an installed npm tree.
            self.assertFalse((out/'node_modules/remotion').exists());self.assertFalse((out/'out').exists())
    def test_registry_cli_outputs_machine_readable_dispatch_receipt(self):
        p=subprocess.run([sys.executable,str(ROOT/'scripts/inspect_comp_coverage.py')],capture_output=True,text=True,timeout=20);self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(json.loads(p.stdout)['dispatch_complete'])

    def test_legacy_golden_source_files_unchanged_in_explicit_context_migration(self):
        old=ROOT/'fixtures/comp_h2';new=ROOT/'fixtures/comp_h9/legacy_qa_compat'
        self.assertEqual((old/'corpus.json').read_bytes(),(new/'corpus.json').read_bytes())
        for case in json.loads((old/'corpus.json').read_text())['cases']:
            a=old/'baselines'/(case['case_id']+'.json')
            prior=json.loads(a.read_text());now=json.loads((new/'baselines'/a.name).read_text())
            self.assertEqual(prior['snapshot']['files'],now['snapshot']['files'])
            self.assertEqual(prior['snapshot']['files_sha256'],now['snapshot']['files_sha256'])
            self.assertNotEqual(prior['snapshot']['context_sha256'],now['snapshot']['context_sha256'])
    def test_old_context_is_rejected_not_silently_blessed(self):
        from bie.compiler.generated_code_regression import baseline_from_dict,evaluate_generated_regression
        from tests.compiler.qa_test_support import bundle
        b=bundle();base=baseline_from_dict(json.loads((ROOT/'fixtures/comp_h2/baselines/math-plain.json').read_text()))
        r=evaluate_generated_regression(files=b.codegen.files,context=b.context,baseline=base,require_full_typecheck=False)
        self.assertFalse(r.source_checks_passed)
        self.assertIn('REGRESSION_CONTEXT_MISMATCH',{f.code for f in r.source_findings})
