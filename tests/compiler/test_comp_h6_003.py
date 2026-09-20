from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import io,os,struct,tempfile,unittest,wave
from bie.compiler.frame_runtime_contract import plan_frame_runtime,CompilerQAError
from bie.compiler.narration_assets import verified_asset_bytes,inspect_pcm,stage_verified_assets
from tests.compiler.h6_test_support import *

class NarrationAssetTests(unittest.TestCase):
    def setUp(self):
        self.p,self.assets=narration_scene();self.plan=plan_frame_runtime(self.p,BIG)
        self.tmp=tempfile.TemporaryDirectory();self.root=write_assets(Path(self.tmp.name)/'assets',self.assets);self.file=self.root/next(iter(self.assets))
    def tearDown(self):self.tmp.cleanup()
    def test_actual_pcm_bytes_verified(self):
        b,r=verified_asset_bytes(self.plan,self.root);self.assertEqual(b,self.assets);self.assertEqual(r['assets'][0]['frame_count'],96000);self.assertFalse(r['accepted'])
    def test_source_root_required(self):
        with self.assertRaisesRegex(CompilerQAError,'ROOT_REQUIRED'):verified_asset_bytes(self.plan,None)
    def test_no_audio_needs_no_root(self):
        self.assertEqual(verified_asset_bytes(plan_frame_runtime(state_scene(),BIG),None)[1]['status'],'NOT_REQUIRED')
    def test_missing_asset_fails(self):
        self.file.unlink()
        with self.assertRaisesRegex(CompilerQAError,'UNAVAILABLE'):verified_asset_bytes(self.plan,self.root)
    def test_same_size_tamper_fails(self):
        b=bytearray(self.file.read_bytes());b[-1]^=1;self.file.write_bytes(b)
        with self.assertRaisesRegex(CompilerQAError,'HASH_MISMATCH'):verified_asset_bytes(self.plan,self.root)
    def test_truncated_asset_fails(self):
        self.file.write_bytes(self.file.read_bytes()[:-2])
        with self.assertRaisesRegex(CompilerQAError,'HASH_MISMATCH'):verified_asset_bytes(self.plan,self.root)
    def test_file_growth_fails_before_unbounded_read(self):
        self.file.write_bytes(self.file.read_bytes()+b'extra')
        with self.assertRaisesRegex(CompilerQAError,'ASSET_SIZE'):verified_asset_bytes(self.plan,self.root)
    def test_final_symlink_fails(self):
        target=Path(self.tmp.name)/'original';self.file.rename(target);self.file.symlink_to(target)
        with self.assertRaisesRegex(CompilerQAError,'UNAVAILABLE'):verified_asset_bytes(self.plan,self.root)
    def test_parent_symlink_fails(self):
        folder=self.file.parent;target=Path(self.tmp.name)/'linked';folder.rename(target);folder.symlink_to(target,target_is_directory=True)
        with self.assertRaisesRegex(CompilerQAError,'UNAVAILABLE'):verified_asset_bytes(self.plan,self.root)
    def test_root_symlink_fails(self):
        link=Path(self.tmp.name)/'alias';link.symlink_to(self.root,target_is_directory=True)
        with self.assertRaisesRegex(CompilerQAError,'ASSET_ROOT'):verified_asset_bytes(self.plan,link)
    def test_fifo_is_rejected_without_blocking(self):
        self.file.unlink();os.mkfifo(self.file)
        with self.assertRaisesRegex(CompilerQAError,'ASSET_SIZE'):verified_asset_bytes(self.plan,self.root)
    def test_declared_sample_rate_not_trusted(self):
        self.plan['audio_assets'][0]['sample_rate']=44100
        with self.assertRaisesRegex(CompilerQAError,'METADATA_MISMATCH'):verified_asset_bytes(self.plan,self.root)
    def test_declared_duration_not_trusted(self):
        self.plan['audio_assets'][0]['frame_count']-=1
        with self.assertRaisesRegex(CompilerQAError,'METADATA_MISMATCH'):verified_asset_bytes(self.plan,self.root)
    def test_pcm_reader_rejects_wrong_container(self):
        with self.assertRaisesRegex(CompilerQAError,'PCM_HEADER'):inspect_pcm(b'not audio'*30)
    def test_pcm_riff_size_binding(self):
        with self.assertRaisesRegex(CompilerQAError,'PCM_HEADER'):inspect_pcm(self.file.read_bytes()+b'x')
    def test_stereo_supported(self):
        meta,data=inspect_pcm(wav_signal(channels=2));self.assertEqual(meta['channels'],2);self.assertEqual(len(data),96000*4)
    def test_44100_hz_samples_not_rounded_duration(self):
        meta,_=inspect_pcm(wav_signal(rate=44100));self.assertEqual(meta['frame_count'],88200)
    def test_unsupported_8bit_rejected(self):
        b=io.BytesIO()
        with wave.open(b,'wb') as w:w.setnchannels(1);w.setsampwidth(1);w.setframerate(8000);w.writeframes(b'\x80'*8000)
        with self.assertRaisesRegex(CompilerQAError,'PCM_FORMAT'):inspect_pcm(b.getvalue())
    def test_staging_preserves_exact_audio_bytes(self):
        b,_=verified_asset_bytes(self.plan,self.root);out=Path(self.tmp.name)/'stage';out.mkdir();stage_verified_assets(b,out)
        for name,data in b.items():self.assertEqual((out/'public'/name).read_bytes(),data)
    def test_staging_never_overwrites(self):
        b,_=verified_asset_bytes(self.plan,self.root);out=Path(self.tmp.name)/'stage';out.mkdir();stage_verified_assets(b,out)
        with self.assertRaises(FileExistsError):stage_verified_assets(b,out)

if __name__=='__main__':unittest.main()
