from copy import deepcopy
from pathlib import Path
import json,shutil,subprocess,sys,tempfile,unittest
from bie.compiler.layout_repair import repair_and_publish,verify_repaired_workspace
from bie.compiler.hardened_scene_compile import require_h3_workspace
from tests.compiler.h4_test_support import text_case,TARGET_BIG,ROOT

class RepairPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.base=Path(cls.tmp.name)
        cls.p,cls.policy=text_case();cls.result=repair_and_publish(cls.p,cls.policy,cls.base/'published',cls.base/'evidence',target=TARGET_BIG)
        if not cls.result['source_published']:raise AssertionError(cls.result)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def setUp(self):
        self.tmp2=tempfile.TemporaryDirectory();self.root=Path(self.tmp2.name)/'source';shutil.copytree(self.base/'published',self.root)
    def tearDown(self):self.tmp2.cleanup()
    def edit_report(self,callback):
        p=self.root/'validation-runs/h4-layout-repair/REPAIR_RESULT.json';r=json.loads(p.read_text());callback(r);p.write_text(json.dumps(r))
    def test_real_local_repair_publishes_source(self):self.assertEqual(self.result['status'],'LOCAL_MEASURED_CANDIDATE');self.assertTrue(self.result['source_published'])
    def test_source_pass_not_render_acceptance(self):
        receipt=require_h3_workspace(self.root);self.assertTrue(receipt.source_gate_passed);self.assertFalse(receipt.full_compile_verified);self.assertFalse(receipt.accepted)
    def test_repair_evidence_revalidates(self):self.assertTrue(verify_repaired_workspace(self.root)['source_recomputed'])
    def test_no_external_attestation_claim(self):self.assertFalse(verify_repaired_workspace(self.root)['actual_measurement_attested'])
    def test_original_text_preserved_in_published_scene(self):
        d=json.loads((self.root/'CHECKED_SCENE.json').read_text());self.assertEqual(d['document']['elements'][0]['props']['text'],self.p['elements'][0]['props']['text'])
    def test_generated_source_tamper_blocked(self):
        p=self.root/'src/Scene.tsx';p.write_text(p.read_text()+'\n//tamper')
        with self.assertRaisesRegex(ValueError,'TAMPERED'):verify_repaired_workspace(self.root)
    def test_original_evidence_tamper_blocked(self):
        p=self.root/'validation-runs/h4-layout-repair/ORIGINAL_SCENE.json';d=json.loads(p.read_text());d['title']='Changed';p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):verify_repaired_workspace(self.root)
    def test_effective_evidence_tamper_blocked(self):
        p=self.root/'validation-runs/h4-layout-repair/EFFECTIVE_SCENE.json';d=json.loads(p.read_text());d['elements'][0]['props']['text']='Less content';p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):verify_repaired_workspace(self.root)
    def test_fake_real_render_claim_rejected(self):
        self.edit_report(lambda r:r.update(real_remotion=True))
        with self.assertRaises(ValueError):verify_repaired_workspace(self.root)
    def test_fake_acceptance_rejected(self):
        self.edit_report(lambda r:r.update(accepted=True))
        with self.assertRaises(ValueError):verify_repaired_workspace(self.root)
    def test_target_switch_rejected(self):
        self.edit_report(lambda r:r['target'].update(width=640))
        with self.assertRaisesRegex(ValueError,'TARGET_IDENTITY'):verify_repaired_workspace(self.root)
    def test_measured_content_tamper_rejected(self):
        folder=self.root/'validation-runs/h4-layout-repair'/('candidate-'+format(self.result['selected_index'],'03d'));f=folder/'MEASUREMENTS.json';m=json.loads(f.read_text());m['records'][0]['rendered_text']=[];f.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'MEASUREMENT_CHANGED'):verify_repaired_workspace(self.root)
    def test_added_executable_is_not_allowed(self):
        (self.root/'evil.ts').write_text('export const x=1;')
        with self.assertRaisesRegex(ValueError,'UNINSPECTED'):verify_repaired_workspace(self.root)
    def test_existing_actual_render_harness_remains_blocked(self):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/validate_checked_remotion.py'),str(self.root)],capture_output=True,text=True,timeout=35)
        d=json.loads(r.stdout);self.assertEqual(r.returncode,2,r.stderr);self.assertIn('FULL_TYPECHECK_BLOCKED',d['failure']);self.assertFalse(d['passed'])
    def test_cli_reports_environment_block_without_false_publish(self):
        folder=Path(self.tmp2.name);s=folder/'scene.json';q=folder/'policy.json';s.write_text(json.dumps(self.p));q.write_text(json.dumps(self.policy))
        r=subprocess.run([sys.executable,str(ROOT/'scripts/repair_scene_layout.py'),str(s),str(folder/'out'),'--policy',str(q),'--evidence',str(folder/'measure'),'--browser','/missing/chromium'],capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,3);self.assertFalse(json.loads(r.stdout)['source_published']);self.assertFalse((folder/'out').exists())
    def test_checked_cli_repair_mode_requires_evidence(self):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/compile_scene_checked.py'),'missing','out','--layout-policy','missing-policy'],capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,2);self.assertIn('layout-evidence',r.stdout)

if __name__=='__main__':unittest.main()
