from pathlib import Path
from dataclasses import asdict,replace
from unittest.mock import patch
import json,sys,tempfile,unittest,subprocess
from bie.compiler.checked_scene_compile import *
from bie.compiler.render_contracts import RenderRequest
from bie.compiler.remotion_composition_discovery import CompositionDescriptor
from bie.compiler.full_render import full_render
from bie.compiler.qa_scene_compile import compile_scene_for_qa
from bie.compiler.capability_fallback_qa import inspect_emitted_semantics
from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
from tests.compiler.h1_test_support import scene,ROOT

class CheckedCompilationTests(unittest.TestCase):
    def p(self):return scene('text',{'text':'Synthetic checked source'})
    def test_valid_source_gate(self):self.assertTrue(compile_scene_checked(self.p())[1].source_gate_passed)
    def test_gate_not_acceptance(self):
        _,r=compile_scene_checked(self.p());self.assertFalse(r.accepted);self.assertFalse(r.full_compile_verified);self.assertEqual(r.real_render_status,'NOT_RUN')
    def test_invalid_topology_blocks_whole_scene(self):
        _,r=compile_scene_checked(scene('model2d',{'vertices':[[0,0],[1,1]],'edges':[[0,8]]}));self.assertFalse(r.source_gate_passed)
    def test_h2_typesetting_closes_supported_latex_defect(self):self.assertTrue(compile_scene_checked(scene('equation',{'expression':'x^2','format':'latex'}))[1].source_gate_passed)
    def test_missing_projection_blocks(self):self.assertFalse(compile_scene_checked(scene('vector',{'components':[1,2,3]}))[1].source_gate_passed)
    def test_simulation_state_dump_blocks(self):self.assertFalse(compile_scene_checked(scene('simulation',{'model_ref':'toy','initial_state':{}},case_id='reject-state-only-simulation'))[1].source_gate_passed)
    def test_geographic_crs_blocks(self):self.assertFalse(compile_scene_checked(scene('map',{'crs':'EPSG:4326','layers':[{'kind':'route','points':[[0,0],[1,1]]}]}))[1].source_gate_passed)
    def test_dense_chart_blocks(self):self.assertFalse(compile_scene_checked(scene('chart',{'chart_kind':'bar','categories':['a']*13,'values':[1]*13}))[1].source_gate_passed)
    def test_missing_actual_parser_blocks(self):
        from bie.compiler.generated_code_regression import probe_typescript_sources
        real=probe_typescript_sources((('x.ts','const x=1'),),typescript_library='/nonexistent/parser')
        with patch('bie.compiler.checked_scene_compile.probe_typescript_sources',return_value=real):self.assertFalse(compile_scene_checked(self.p())[1].source_gate_passed)
    def test_publish_and_verify(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source';r=publish_checked_scene(self.p(),p);self.assertEqual(verify_checked_workspace(p),r)
    def test_invalid_source_never_materialized(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source'
            with self.assertRaises(ValueError):publish_checked_scene(scene('vector',{'components':[1,2,3]}),p)
            self.assertFalse(p.exists())
    def test_existing_destination_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source';p.mkdir();(p/'keep').write_text('keep')
            with self.assertRaises(ValueError):publish_checked_scene(self.p(),p)
            self.assertEqual((p/'keep').read_text(),'keep')
    def test_tampered_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source';publish_checked_scene(self.p(),p);(p/'src/Root.tsx').write_text('malicious')
            with self.assertRaisesRegex(ValueError,'TAMPERED'):verify_checked_workspace(p)
    def test_hidden_added_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source';publish_checked_scene(self.p(),p);(p/'extra.ts').write_text('export {}')
            with self.assertRaisesRegex(ValueError,'UNINSPECTED'):verify_checked_workspace(p)
    def test_uninspected_config_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source';publish_checked_scene(self.p(),p);(p/'webpack.config.js').write_text('export {}')
            with self.assertRaises(ValueError):verify_checked_workspace(p)
    def test_receipt_acceptance_cannot_be_forged(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source';publish_checked_scene(self.p(),p);q=p/'CHECKED_SCENE.json';data=json.loads(q.read_text());data['receipt']['accepted']=True;q.write_text(json.dumps(data))
            with self.assertRaises(ValueError):verify_checked_workspace(p)
    def test_missing_marker_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'CHECKED_SCENE_REQUIRED'):verify_checked_workspace(Path(td))
    def test_changed_codegen_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source';publish_checked_scene(self.p(),p);(p/'CODEGEN_MANIFEST.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'MANIFEST_TAMPERED'):verify_checked_workspace(p)
    def test_symlink_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source';publish_checked_scene(self.p(),p);q=p/'src/Root.tsx';other=Path(td)/'r.tsx';other.write_bytes(q.read_bytes());q.unlink();q.symlink_to(other)
            with self.assertRaises(ValueError):verify_checked_workspace(p)
    def test_scene_fingerprint_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source';publish_checked_scene(self.p(),p)
            with self.assertRaises(ValueError):verify_checked_workspace(p,expected_scene_fingerprint='f'*64)
    def test_changed_source_with_new_hash_not_enough(self):
        from hashlib import sha256
        p=self.p();b=compile_scene_for_qa(p);r=b.element_results[0];bad=replace(r,source_text=r.source_text+'//changed\n',source_sha256=sha256((r.source_text+'//changed\n').encode()).hexdigest())
        self.assertIn('HARDENED_EMITTER_OUTPUT_MISMATCH',{f.code for f in inspect_emitted_semantics(decode_scene_ir(p),(bad,))})
    def test_real_render_api_cannot_bypass_source_gate(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'package.json').write_text('{}')
            request=RenderRequest(workspace=str(p),entrypoint='src/index.ts',composition=CompositionDescriptor('BieTest',640,360,24,24),output_path='out/x.mp4',scene_fingerprint='a'*64,run_id='h1-block')
            r=full_render(request);self.assertFalse(r.passed);self.assertFalse(r.process_started);self.assertEqual(r.failure_code,'SOURCE_QA_BLOCKED')
    def test_cli_rejects_missing_source_marker(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);q=p/'request.json';q.write_text(json.dumps({'workspace':td,'entrypoint':'src/index.ts','composition':{'composition_id':'BieTest','width':640,'height':360,'fps':24,'duration_in_frames':24},'output_path':'out/x.mp4','scene_fingerprint':'a'*64,'run_id':'cli-test'}))
            r=subprocess.run([sys.executable,str(ROOT/'scripts/run_comp_render.py'),str(q),'--mode','full'],capture_output=True,text=True,timeout=15)
            self.assertEqual(r.returncode,2);self.assertIn('CHECKED_SCENE_REQUIRED',r.stderr)
    def test_inert_prior_render_evidence_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source';publish_checked_scene(self.p(),p);(p/'render-evidence/old').mkdir(parents=True);(p/'render-evidence/old/run.json').write_text('{}');self.assertTrue(verify_checked_workspace(p).source_gate_passed)
    def test_executable_in_output_directory_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source';publish_checked_scene(self.p(),p);(p/'out').mkdir();(p/'out/hidden.js').write_text('export {}')
            with self.assertRaises(ValueError):verify_checked_workspace(p)

if __name__=='__main__':unittest.main()
