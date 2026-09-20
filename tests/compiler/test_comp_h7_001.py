import json,tempfile,unittest,subprocess,sys
from pathlib import Path
from copy import deepcopy
from tests.compiler.h7_test_support import dynamic_repair_case,narration_scene,write_assets,BIG
from bie.compiler.layout_repair import repair_and_publish,verify_repaired_workspace
from bie.compiler.layout_repair_contracts import default_policy,verify_repair,semantic_identity
from bie.compiler.hardened_scene_compile import require_h3_workspace

class DynamicRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name)
        cls.p,cls.assets,cls.policy=dynamic_repair_case();cls.asset_root=write_assets(cls.root/'assets',cls.assets)
        cls.result=repair_and_publish(cls.p,cls.policy,cls.root/'published',cls.root/'evidence',target=BIG,asset_root=cls.asset_root,screenshots=False)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_asset_dynamic_repair_publishes(self):self.assertTrue(self.result['source_published'],self.result)
    def test_later_state_preserved(self):
        q=json.loads((self.root/'evidence/EFFECTIVE_SCENE.json').read_text());self.assertEqual(q['events'],self.p['events'])
    def test_narration_contract_unchanged(self):
        q=json.loads((self.root/'evidence/EFFECTIVE_SCENE.json').read_text());self.assertEqual(q['narration_cues'],self.p['narration_cues']);self.assertEqual(q['metadata']['compiler_h6'],self.p['metadata']['compiler_h6'])
    def test_no_shrinking_to_fit(self):
        q=json.loads((self.root/'evidence/EFFECTIVE_SCENE.json').read_text());self.assertTrue(verify_repair(self.p,q,self.policy)['content_preserved'])
    def test_asset_bytes_preserved(self):
        for rel,b in self.assets.items():self.assertEqual((self.root/'published/public'/rel).read_bytes(),b)
    def test_audio_receipt_bound(self):self.assertEqual(self.result['asset_verification']['status'],'PCM_BYTES_VERIFIED_NOT_SPEECH_ALIGNMENT')
    def test_repaired_workspace_revalidates(self):self.assertTrue(verify_repaired_workspace(self.root/'published')['source_recomputed'])
    def test_not_remotion_claim(self):self.assertFalse(self.result['real_remotion']);self.assertFalse(self.result['accepted'])
    def test_missing_assets_block(self):
        with tempfile.TemporaryDirectory() as td:
            r=repair_and_publish(self.p,self.policy,Path(td)/'p',Path(td)/'e',target=BIG)
            self.assertFalse(r['source_published']);self.assertIn('NARRATION_ASSET_ROOT_REQUIRED',r['runtime_block'])
    def test_corrupted_audio_block(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);a=write_assets(p/'a',{rel:b[:-1]+b'0' for rel,b in self.assets.items()})
            r=repair_and_publish(self.p,self.policy,p/'p',p/'e',target=BIG,asset_root=a)
            self.assertFalse(r['source_published']);self.assertIn('HASH_MISMATCH',r['runtime_block'])
    def test_policy_source_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            policy=deepcopy(self.policy);policy['scene_identity']='0'*64
            with self.assertRaisesRegex(ValueError,'SOURCE_MISMATCH'):repair_and_publish(self.p,policy,Path(td)/'p',Path(td)/'e',target=BIG,asset_root=self.asset_root)
    def test_source_audio_tamper_detected(self):
        import shutil
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'copy';shutil.copytree(self.root/'published',p)
            asset=p/'public'/next(iter(self.assets));asset.write_bytes(b'bad')
            with self.assertRaises(ValueError):require_h3_workspace(p)
    def test_current_cli_accepts_asset_and_policy_flags(self):
        code=(Path(__file__).parents[2]/'scripts/compile_scene_checked.py').read_text()
        self.assertNotIn('H6_LAYOUT_REPAIR_ASSET_COMBINATION_PENDING',code);self.assertIn('asset_root=args.asset_root',code)
