import unittest,subprocess,sys,json,tempfile
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from bie.compiler.consumer_coverage import *
from bie.compiler import qa_scene_compile,animation_behavior,specialized_motion
from bie.scene_ir import scene_ir_registry
from bie.compiler.hardened_scene_compile import compile_h3_scene
from tests.compiler.h8_test_support import raw_text,BROWSER,track

class LiveCoverageTests(unittest.TestCase):
    def test_registry_count_is_derived_not_constant(self):r=inspect_consumer_coverage();self.assertEqual(r['registry_elements'],len(scene_ir_registry.ELEMENT_TYPES));self.assertEqual(r['registry_actions'],len(scene_ir_registry.ACTIONS))
    def test_three_former_missing_elements_now_dispatched(self):r=inspect_consumer_coverage();self.assertEqual([x['name'] for x in r['missing'] if x['kind']=='element'],[])
    def test_seven_former_missing_action_names_now_dispatched(self):r=inspect_consumer_coverage();self.assertEqual([x['name'] for x in r['missing'] if x['kind']=='action'],[])
    def test_present_dispatch_not_behavior_completion(self):r=inspect_consumer_coverage();self.assertFalse(r['behavior_coverage_complete']);self.assertTrue(all(x['status'].endswith('NOT_EXHAUSTIVELY_CERTIFIED') for x in r['rows'] if x['dispatch']))
    def test_complete_all_34_rows(self):r=inspect_consumer_coverage();self.assertEqual(len(r['rows']),34);self.assertEqual(len({(x['kind'],x['name']) for x in r['rows']}),34)
    def test_sha_identity_and_relative_sources(self):r=inspect_consumer_coverage();self.assertTrue(r['source_files']);self.assertTrue(all(not x.startswith('/') and len(v)==64 for x,v in r['source_files'].items()))
    def test_repeatable(self):self.assertEqual(inspect_consumer_coverage(),inspect_consumer_coverage())
    def test_no_completion_permission(self):r=inspect_consumer_coverage();self.assertFalse(r['section_exit_permitted']);self.assertTrue(r['dispatch_complete']);self.assertFalse(r['accepted'])
    def test_unmapped_coverage_blocks(self):
        with patch.dict(qa_scene_compile.EMITTERS,{},clear=True):
            self.assertRaisesRegex(ValueError,'REQUIRED_CONSUMERS_MISSING',require_dispatch_coverage,inspect_consumer_coverage())
    def test_forged_pass_blocked(self):r=inspect_consumer_coverage();r['behavior_coverage_complete']=True;self.assertRaisesRegex(ValueError,'STALE_OR_FORGED',require_dispatch_coverage,r)
    def test_new_registry_entry_is_not_silently_covered(self):
        with patch.object(scene_ir_registry,'ELEMENT_TYPES',scene_ir_registry.ELEMENT_TYPES+('new-example',)):
            self.assertIn({'kind':'element','name':'new-example'},inspect_consumer_coverage()['missing'])
    def test_duplicate_registry_rejected(self):
        with patch.object(scene_ir_registry,'ACTIONS',scene_ir_registry.ACTIONS+('enter',)):self.assertRaisesRegex(ValueError,'DUPLICATE',inspect_consumer_coverage)
    def test_removed_consumer_shows_new_gap(self):
        with patch.dict(qa_scene_compile.EMITTERS,{},clear=True):self.assertEqual(len([x for x in inspect_consumer_coverage()['missing'] if x['kind']=='element']),18)
    def test_unregistered_dispatch_is_not_ignored(self):
        with patch.dict(qa_scene_compile.EMITTERS,{'new':qa_scene_compile.EMITTERS['text']}):self.assertEqual(inspect_consumer_coverage()['unregistered_dispatch']['elements'],['new'])
    def test_invalid_dispatch_rejected(self):
        with patch.dict(qa_scene_compile.EMITTERS,{'text':7}):self.assertRaisesRegex(ValueError,'INVALID_DISPATCH',inspect_consumer_coverage)
    def test_same_named_reduced_metadata_is_not_registered_action(self):self.assertNotIn('static_trace',animation_behavior.SUPPORTED_ACTIONS|specialized_motion.ACTIONS)
    def test_missing_elements_reproduced_in_current_compiler(self):
        # H9 migration: incomplete former inputs are now rejected by concrete
        # element contracts, not by an absent dispatch. Exact H8 test is in lineage.
        for kind in ('shape','diagram','highlight'):
            with self.subTest(kind=kind):
                p=raw_text();p['elements'][0].update(element_type=kind,props={})
                result=compile_h3_scene(p,target=BROWSER)
                self.assertFalse(result.receipt.source_gate_passed)
                self.assertNotIn('EMITTER_UNAVAILABLE',[f.code for f in result.receipt.findings])
    def test_missing_actions_reproduced_in_contract_dispatch(self):
        # All original missing names now exist, but empty payloads are not guessed.
        from bie.compiler.registered_actions import ACTIONS
        for name in ACTIONS:
            with self.subTest(action=name),self.assertRaisesRegex(ValueError,'ACTION_UNSUPPORTED'):
                animation_behavior.motion_contract(track(name,{},element_id='e0'))
    def test_coverage_cli_now_passes_dispatch_only(self):
        root=Path(__file__).parents[2]
        p=subprocess.run([sys.executable,str(root/'scripts/inspect_comp_coverage.py')],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(json.loads(p.stdout)['dispatch_complete'])
