import unittest,hashlib,json
from bie.audio.common import AudioError
from bie.audio.compiler_handoff import build_compiler_handoff,validate_compiler_handoff,CANONICAL_MAIN,CANONICAL_BLOBS
from tests.audio.h10_test_support import baseline,compiler

class CompilerHandoffTests(unittest.TestCase):
    def setUp(self):self.files,self.bundle,self.plan,self.utts=baseline();self.receipt,self.assets=compiler()
    def test_01_pinned_canonical_main(self):self.assertEqual(self.receipt['canonical_main'],CANONICAL_MAIN)
    def test_02_pinned_blob_inventory(self):self.assertEqual(self.receipt['canonical_compiler_blobs'],CANONICAL_BLOBS)
    def test_03_compiler_schema(self):self.assertEqual(self.receipt['compiler_h6']['schema_version'],'bie.comp-frame-runtime.v1')
    def test_04_asset_content_addressed(self):
        a=self.receipt['compiler_h6']['audio_assets'][0];self.assertEqual(a['public_path'],'narration/'+a['sha256']+'.wav');self.assertEqual(hashlib.sha256(self.assets[a['public_path']]).hexdigest(),a['sha256'])
    def test_05_pcm_contract(self):
        a=self.receipt['compiler_h6']['audio_assets'][0];self.assertEqual((a['sample_rate'],a['channels'],a['sample_width']),(22050,1,2))
    def test_06_source_refs_preserved(self):self.assertEqual(self.receipt['compiler_h6']['audio_assets'][0]['source_refs'],['synthetic:audio-fixture:1'])
    def test_07_reasoning_refs_explicit(self):self.assertEqual(self.receipt['compiler_h6']['audio_assets'][0]['reasoning_refs'],['reasoning:synthetic-h5'])
    def test_08_transcript_hash_exact(self):
        s=self.receipt['compiler_h6']['audio_segments'][0];t=next(iter(self.receipt['compiler_h6']['narration_texts'].values()))['text'];self.assertEqual(s['transcript_sha256'],hashlib.sha256(t.encode()).hexdigest())
    def test_09_padding_never_truncates(self):
        e=self.receipt['sample_evidence'][0];self.assertFalse(e['speech_truncated']);self.assertGreaterEqual(e['published_samples'],e['source_samples'])
    def test_10_caption_target_explicit(self):self.assertEqual(self.receipt['compiler_h6']['caption_target_id'],'caption:text')
    def test_11_scene_targets_explicit(self):self.assertEqual(self.receipt['narration_cues'][0]['target_ids'],['visual:primary'])
    def test_12_missing_target_fails(self):
        clock=json.loads(self.files['MIX_CLOCK.json'])
        with self.assertRaisesRegex(AudioError,'COMP_HANDOFF_SCENE_TARGETS'):build_compiler_handoff(self.plan,self.files['master.wav'],clock,fps=24,caption_target_id='caption:text',target_ids_by_scene={},rights_ref='r',reasoning_refs=('x',))
    def test_13_wrong_master_fails(self):
        clock=json.loads(self.files['MIX_CLOCK.json'])
        with self.assertRaises(Exception):build_compiler_handoff(self.plan,b'bad',clock,fps=24,caption_target_id='caption:text',target_ids_by_scene={'scene:1':('v',)},rights_ref='r',reasoning_refs=('x',))
    def test_14_wrong_clock_fails(self):
        clock=json.loads(self.files['MIX_CLOCK.json']);clock['plan_fingerprint']='sha256:'+'0'*64
        with self.assertRaisesRegex(AudioError,'COMP_HANDOFF_CLOCK_BINDING'):build_compiler_handoff(self.plan,self.files['master.wav'],clock,fps=24,caption_target_id='caption:text',target_ids_by_scene={'scene:1':('v',)},rights_ref='r',reasoning_refs=('x',))
    def test_15_tampered_asset_fails(self):
        assets=dict(self.assets);k=next(iter(assets));assets[k]=assets[k]+b'x'
        with self.assertRaisesRegex(AudioError,'COMP_HANDOFF_ASSET_BYTES'):validate_compiler_handoff(self.receipt,assets)
    def test_16_no_remotion_acceptance_claim(self):self.assertFalse(self.receipt['real_remotion_render_verified']);self.assertFalse(self.receipt['product_accepted'])
if __name__=='__main__':unittest.main()
