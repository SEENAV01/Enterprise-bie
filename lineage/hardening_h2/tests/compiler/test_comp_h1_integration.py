from pathlib import Path
from dataclasses import asdict,replace
from hashlib import sha256
import json,math,sys,subprocess,tempfile,unittest
from bie.compiler.checked_scene_compile import *
from bie.compiler.qa_scene_compile import compile_scene_for_qa
from bie.compiler.qa_common import digest
from bie.compiler.chart_geometry import chart_geometry
from bie.compiler.vector_geometry import vector_geometry
from bie.compiler.model2d_geometry import model2d_geometry
from bie.compiler.deterministic_output_qa import snapshot_generated,compare_snapshots
from bie.compiler.compile_diagnostics_mapping import validate_source_map
from bie.compiler.render_contracts import RenderRequest
from bie.compiler.remotion_composition_discovery import CompositionDescriptor
from bie.compiler.full_render import full_render
from tests.compiler.h1_test_support import ROOT,scene

class H1IntegrationTests(unittest.TestCase):
    def p(self):return scene('text',{'text':'Technical fixture'})
    def request(self,root,p):
        return RenderRequest(workspace=str(root),entrypoint='src/index.ts',composition=CompositionDescriptor('BieQA'+digest(p['scene_id'])[:16],640,360,24,(p['duration_ms']*24+999)//1000),output_path='out/test.mp4',scene_fingerprint=compile_scene_for_qa(p).scene_fingerprint,run_id='h1-integration')
    def test_checked_validation_harness_stops_honestly_without_dependencies(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'source';publish_checked_scene(self.p(),root)
            run=subprocess.run([sys.executable,str(ROOT/'scripts/validate_checked_remotion.py'),str(root)],capture_output=True,text=True,timeout=20)
            raw=json.loads(run.stdout)
            self.assertEqual(run.returncode,2,run.stderr);self.assertFalse(raw['passed']);self.assertFalse(raw['accepted'])
            self.assertIn('FULL_TYPECHECK_BLOCKED',raw['failure'])
            self.assertFalse(any(x['stage']=='real-cli-composition-discovery' for x in raw['stages']))
    def test_checked_validation_harness_rejects_legacy_unchecked_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            run=subprocess.run([sys.executable,str(ROOT/'scripts/validate_checked_remotion.py'),td],capture_output=True,text=True,timeout=20)
            raw=json.loads(run.stdout);self.assertEqual(run.returncode,2);self.assertIn('CHECKED_SCENE_REQUIRED',raw['failure'])
    def test_new_emitters_strict_tsc_with_explicit_ambient_test_doubles(self):
        from bie.compiler.chart_compiler import compile_chart_element
        from bie.compiler.vector_compiler import compile_vector_element
        from bie.compiler.model2d_compiler import compile_model2d_element
        from tests.compiler.h1_test_support import element
        results=[]
        for kind in ('bar','line','area','scatter','pie'):
            props={'chart_kind':kind,'categories':['a','b'],'values':[1,3]}
            if kind=='scatter':props['x_values']=[-2,4]
            results.append(compile_chart_element(element('chart',props,eid=kind)))
        results.append(compile_vector_element(element('vector',{'components':[0,0]},eid='zero')))
        results.append(compile_model2d_element(element('model2d',{'vertices':[[0,0],[1,1]],'edges':[]},eid='isolated')))
        # This real tsc run checks our internal expressions/types ONLY. These ambient
        # test doubles do NOT verify the installed React/Remotion APIs or full project.
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for i,r in enumerate(results):(root/f'component{i}.tsx').write_text(r.source_text)
            (root/'ambient.d.ts').write_text("""declare module 'react' { namespace React { type FC = () => unknown; } export = React; }
declare module 'react/jsx-runtime' { export namespace JSX { interface IntrinsicElements { [name:string]: any; } } }
""")
            run=subprocess.run(['tsc','--noEmit','--strict','--esModuleInterop','--moduleResolution','node','--target','ES2022','--jsx','react-jsx',*map(str,sorted(root.glob('*')))],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
    def test_original_qa_corpus_and_goldens_unchanged(self):
        manifest=json.loads((ROOT/'lineage/batch_009/ORIGINAL_MEMBER_HASHES.json').read_text())
        for rel,h in manifest.items():
            if rel.startswith('fixtures/comp_qa_009/'):
                self.assertEqual(sha256((ROOT/rel).read_bytes()).hexdigest(),h,rel)
    def test_each_changed_parent_python_file_has_original_bytes(self):
        manifest=json.loads((ROOT/'lineage/batch_009/ORIGINAL_MEMBER_HASHES.json').read_text())
        for rel,h in manifest.items():
            if rel.endswith('.py') and sha256((ROOT/rel).read_bytes()).hexdigest()!=h:
                candidates=[ROOT/'lineage/batch_009'/rel,ROOT/'lineage/hardening_h1'/rel]
                self.assertTrue(any(p.is_file() and sha256(p.read_bytes()).hexdigest()==h for p in candidates),rel)
    def test_checked_cli_uses_real_parser_and_publishes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'scene.json').write_text(json.dumps(self.p()))
            run=subprocess.run([sys.executable,str(ROOT/'scripts/compile_scene_checked.py'),str(root/'scene.json'),str(root/'output')],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr);self.assertFalse(json.loads(run.stdout)['accepted']);self.assertTrue(verify_checked_workspace(root/'output').source_gate_passed)
    def test_matched_source_request_stops_at_missing_real_dependencies(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'source';p=self.p();publish_checked_scene(p,root);r=full_render(self.request(root,p))
            self.assertFalse(r.passed);self.assertFalse(r.process_started);self.assertEqual(r.failure_code,'FULL_TYPECHECK_BLOCKED')
    def test_composition_dimensions_cannot_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'source';p=self.p();publish_checked_scene(p,root);req=self.request(root,p)
            req=replace(req,composition=replace(req.composition,width=1280))
            with self.assertRaisesRegex(ValueError,'SOURCE_MISMATCH'):verify_checked_workspace(root,render_request=req)
    def test_unbound_runtime_props_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'source';p=self.p();publish_checked_scene(p,root);req=replace(self.request(root,p),props_file='props.json')
            with self.assertRaisesRegex(ValueError,'PROPS_NOT_BOUND'):verify_checked_workspace(root,render_request=req)
    def test_unsafe_integer_not_rounded_silently(self):
        with self.assertRaisesRegex(ValueError,'PRECISION_UNSUPPORTED'):chart_geometry({'chart_kind':'bar','categories':['a'],'values':[9007199254740993]})
    def test_undeclared_log_scale_not_ignored(self):
        with self.assertRaisesRegex(ValueError,'UNCONSUMED_ELEMENT_PROPERTY'):chart_geometry({'chart_kind':'bar','categories':['a'],'values':[1],'scale':'log'})
    def test_unsupported_vector_origin_not_ignored(self):
        with self.assertRaises(ValueError):vector_geometry({'components':[1,2],'origin':[4,5]})
    def test_directed_topology_not_claimed_by_undirected_model(self):
        with self.assertRaises(ValueError):model2d_geometry({'vertices':[[0,0],[1,1]],'edges':[[0,1]],'directed':True})
    def test_fixed_families_keep_source_mapping(self):
        p=scene('chart',{'chart_kind':'line','categories':['a','b'],'values':[-2,3]});b=compile_scene_for_qa(p);validate_source_map(b.source_map,b.codegen.files)
        self.assertTrue(all(s.origin.source_refs for s in b.source_map.spans))
    def test_fixed_chart_byte_determinism(self):
        p=scene('chart',{'chart_kind':'pie','categories':['a','b'],'values':[2,3]});a=compile_scene_for_qa(p);b=compile_scene_for_qa(p)
        self.assertTrue(compare_snapshots((snapshot_generated(a.codegen.files,a.context),snapshot_generated(b.codegen.files,b.context)),expected_runs=2).passed)
    def test_old_defective_line_is_still_rejected(self):
        from tests.compiler.qa_test_support import historical_semantics
        codes={f.code for f in historical_semantics('reject-chart-kind')};self.assertIn('CHART_KIND_DOWNGRADE',codes);self.assertIn('HARDENED_EMITTER_OUTPUT_MISMATCH',codes)
    def test_known_fixed_input_now_passes_without_regression_error(self):
        from tests.compiler.qa_test_support import bundle
        self.assertTrue(bundle('reject-jsx-braces').source_contract_passed);self.assertTrue(bundle('reject-chart-sign').source_contract_passed)
    def test_contract_error_stub_is_not_published(self):
        p=scene('model2d',{'vertices':[[0,0],[1,1]],'edges':[[0,9]]});b=compile_scene_for_qa(p)
        self.assertIn('throw new Error',b.element_results[0].source_text);self.assertFalse(b.source_contract_passed)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):publish_checked_scene(p,Path(td)/'blocked')
    def test_new_corpus_expected_fixes_are_not_new_input_replacements(self):
        old=json.loads((ROOT/'fixtures/comp_qa_009/corpus.json').read_text())['cases'];new=json.loads((ROOT/'fixtures/comp_h1/corpus.json').read_text())['cases']
        self.assertEqual([c['document'] for c in old],[c['document'] for c in new]);self.assertEqual(sum(c['expected_source_passed'] for c in new),13)

if __name__=='__main__':unittest.main()
