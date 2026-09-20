import json,tempfile,unittest,shutil,subprocess
from pathlib import Path
from dataclasses import asdict,replace
from bie.compiler.real_paint import *
from bie.compiler.hardened_scene_compile import publish_h3_scene
from tests.compiler.h6_test_support import state_scene,BIG

class RealProducerTests(unittest.TestCase):
    def test_json_cannot_authorize(self):
        with self.assertRaisesRegex(ValueError,'WITNESS_REQUIRED'):require_actual_witness({'passed':True},'a')
    def test_forged_dataclass_cannot_authorize(self):
        with self.assertRaisesRegex(ValueError,'WITNESS_REQUIRED'):require_actual_witness(ActualPaintWitness('a',digest({}),'b',1,True,{},object()),'a')
    def test_stale_manifest_reject(self):
        from bie.compiler.real_paint import _SEAL
        w=ActualPaintWitness('a',digest({}),'b',1,True,{},_SEAL)
        with self.assertRaisesRegex(ValueError,'WITNESS_REQUIRED'):require_actual_witness(w,'other')
    def test_mutated_evidence_reject(self):
        from bie.compiler.real_paint import _SEAL
        e={'v':1};w=ActualPaintWitness('a',digest(e),'b',1,True,e,_SEAL);e['v']=2
        with self.assertRaisesRegex(ValueError,'WITNESS_REQUIRED'):require_actual_witness(w,'a')
    def test_failed_witness_reject(self):
        from bie.compiler.real_paint import _SEAL
        with self.assertRaisesRegex(ValueError,'WITNESS_REQUIRED'):require_actual_witness(ActualPaintWitness('a',digest({}),'b',1,False,{},_SEAL),'a')
    def test_capture_uses_original_scene(self):
        s=capture_entry({'nonce':'test'},'x=>[]','x=>[]');self.assertIn('import {Scene} from "./src/Scene"',s);self.assertIn('<><Scene/><Observer/></>',s)
    def test_capture_prefix_not_replaced(self):
        s=capture_entry({'nonce':'test'},'x=>[]','x=>[]');self.assertIn('BIE_PAINT_V1:',s);self.assertNotIn('const req = REQUEST',s)
    def test_capture_waits_fonts_and_paint(self):
        s=capture_entry({},'x=>[]','x=>[]');self.assertIn('await document.fonts.ready',s);self.assertIn('requestAnimationFrame(()=>requestAnimationFrame',s);self.assertIn('delayRender',s)
    def test_actual_cjs_syntax_real_node(self):
        p=Path(__file__).parents[2]/'bie/compiler/qa_support/remotion_paint_capture.cjs';r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
    def test_actual_entry_has_no_double_import(self):
        p=Path(__file__).parents[2]/'bie/compiler/qa_support/remotion_paint_capture.cjs';s=p.read_text();self.assertIn('@remotion/renderer',s);self.assertIn('@remotion/bundler',s);self.assertNotIn('layout_bridge',s);self.assertIn('renderStill',s);self.assertIn('renderMedia',s)
    def test_missing_project_deps_blocks_typecheck(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);publish_h3_scene(state_scene(),p/'s',target=BIG)
            r=isolated_typecheck(p/'s',node=shutil.which('node'),evidence_directory=p/'tc')
            self.assertEqual(r.status,'BLOCKED_DEPENDENCIES');self.assertEqual(json.loads((p/'tc/TYPECHECK.json').read_text())['executions'],[])
    def test_mismatched_target_blocks_producer(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);publish_h3_scene(state_scene(),p/'s',target=BIG)
            with self.assertRaisesRegex(ValueError,'TARGET_MISMATCH'):produce_actual_paint(p/'s',p/'out',node=shutil.which('node'),browser='/usr/bin/chromium',target=replace(BIG,width=640))
    def test_missing_lock_never_falls_back(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);publish_h3_scene(state_scene(),p/'s',target=BIG)
            with self.assertRaises(ValueError):produce_actual_paint(p/'s',p/'out',node=shutil.which('node'),browser='/usr/bin/chromium',target=BIG)
            self.assertFalse((p/'out/EVIDENCE.json').exists())
    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'o').mkdir()
            with self.assertRaisesRegex(ValueError,'OUTPUT_EXISTS'):produce_actual_paint(p/'missing',p/'o',node=shutil.which('node'),browser='/usr/bin/chromium',target=BIG)
    def test_output_symlink_reject(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'o').symlink_to(p/'x')
            with self.assertRaisesRegex(ValueError,'SYMLINK'):produce_actual_paint(p/'missing',p/'o',node=shutil.which('node'),browser='/usr/bin/chromium',target=BIG)
