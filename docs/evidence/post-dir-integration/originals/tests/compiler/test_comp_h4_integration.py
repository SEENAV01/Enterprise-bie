from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import json,subprocess,sys,tempfile,unittest
from bie.compiler.layout_repair_contracts import candidates,verify_repair,canonical_scene
from bie.compiler.hardened_scene_compile import compile_h3_scene,publish_h3_scene
from bie.compiler.compile_diagnostics_mapping import validate_source_map
from bie.compiler.generated_code_regression import probe_typescript_sources
from tests.compiler.h4_test_support import text_case,map_case,equation_case,TARGET_BIG,ROOT

class H4IntegrationTests(unittest.TestCase):
    def test_full_source_map_retains_provenance(self):
        p,q=map_case();r=compile_h3_scene(list(candidates(p,q))[1].document,target=TARGET_BIG);validate_source_map(r.bundle.source_map,r.codegen.files);self.assertTrue(all(s.origin.source_refs and s.origin.reasoning_refs for s in r.bundle.source_map.spans))
    def test_legacy_corpora_remain_byte_identical(self):
        rows=json.loads((ROOT/'lineage/hardening_h3/ORIGINAL_MEMBER_HASHES.json').read_text())['members']
        for row in rows:
            if row['path'].startswith('fixtures/'):
                self.assertEqual(sha256((ROOT/row['path']).read_bytes()).hexdigest(),row['sha256'],row['path'])
    def test_changed_active_parent_files_preserved(self):
        rows=json.loads((ROOT/'lineage/hardening_h3/ORIGINAL_MEMBER_HASHES.json').read_text())['members']
        for row in rows:
            if row['path'].startswith(('app/','tests/','scripts/')):
                p=ROOT/row['path'];self.assertTrue(p.is_file())
                if sha256(p.read_bytes()).hexdigest()!=row['sha256']:
                    self.assertEqual(sha256((ROOT/'lineage/hardening_h3'/row['path']).read_bytes()).hexdigest(),row['sha256'])
    def test_map_style_change_does_not_reproject(self):
        from bie.compiler.map_geometry import map_geometry
        p,q=map_case();c=list(candidates(p,q))[1];e=dict(c.document['elements'][0]['props']);e.pop('compiler_layout');self.assertEqual(map_geometry(e),map_geometry(p['elements'][0]['props']))
    def test_equation_resize_does_not_rewrite_expression(self):
        p,q=equation_case();c=list(candidates(p,q))[-1];self.assertEqual(p['elements'][0]['props'],c.document['elements'][0]['props']);self.assertFalse(c.invariants['learning_equivalence_verified'])
    def test_all_candidates_have_same_semantic_identity(self):
        p,q=text_case();self.assertEqual(len({c.invariants['semantic_identity'] for c in candidates(p,q)}),1)
    def test_candidate_manifests_repeat_in_independent_process(self):
        p,q=map_case();c=list(candidates(p,q))[1];r=compile_h3_scene(c.document,target=TARGET_BIG)
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'input.json';f.write_text(json.dumps(c.document))
            code="import json,sys;from dataclasses import replace;from bie.compiler.qa_scene_compile import CompilerQATarget;from bie.compiler.hardened_scene_compile import compile_h3_scene;r=compile_h3_scene(json.load(open(sys.argv[1])),target=replace(CompilerQATarget(),compiler_version='1.3.0-comp-h3',width=1280,height=720));print(r.codegen.manifest_sha256)"
            child=subprocess.run([sys.executable,'-c',code,str(f)],capture_output=True,text=True,timeout=30,cwd=ROOT)
            self.assertEqual(child.returncode,0,child.stderr);self.assertEqual(child.stdout.strip(),r.codegen.manifest_sha256)
    def test_no_model_or_timing_mutation_to_make_fit(self):
        p,q=text_case();c=list(candidates(p,q))[-1].document;c['duration_ms']+=1
        with self.assertRaisesRegex(ValueError,'SEMANTIC_CHANGE'):verify_repair(p,c,q)

if __name__=='__main__':unittest.main()
