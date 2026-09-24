"""Assets, source identities, exclusive publication, and actual CLI failures."""
from dataclasses import asdict, replace
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile,unittest
from bie.audio.common import AudioError,fingerprint
from bie.audio.mix_io import read_mix_spec,publish_mix
from bie.audio.mix_pipeline import mix_synchronized,MixPolicy
from bie.audio.loudness_normalization import LoudnessPolicy
from .mix_test_support import real_sync,stem,tone,spec,ROOT

class MixIOTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sync=real_sync();cls.result=mix_synchronized(cls.sync)
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        pcm=tone(frames=800,amp=.01);data=pcm.to_wav();(self.root/'cue.wav').write_bytes(data)
        self.row={**{k:v for k,v in asdict(stem(pcm,start_sample=4000)).items() if k!='pcm'},'path':'cue.wav','sha256':hashlib.sha256(data).hexdigest(),'sample_rate':22050,'channels':1}
        self.row['source_refs']=list(self.row['source_refs']);self.raw=spec(self.sync,(self.row,))
    def tearDown(self):self.temp.cleanup()
    def read(self):return read_mix_spec(self.raw,self.root,self.sync)
    def test_actual_wav_loaded_with_exact_bytes(self):
        stems,policy,copies=self.read();self.assertEqual(len(stems),1)
        self.assertEqual(copies[self.row['sha256']+'.wav'],(self.root/'cue.wav').read_bytes())
    def test_missing_file(self):
        (self.root/'cue.wav').unlink()
        with self.assertRaises((AudioError,OSError)):self.read()
    def test_changed_file_hash(self):
        (self.root/'cue.wav').write_bytes(tone(frames=800,amp=.02).to_wav())
        with self.assertRaisesRegex(AudioError,'HASH'):self.read()
    def test_path_traversal(self):
        for name in ('../cue.wav','/tmp/cue.wav','a/../cue.wav','./cue.wav','a\\cue.wav','a//cue.wav'):
            with self.subTest(name=name):
                self.row['path']=name
                with self.assertRaises(AudioError):self.read()
    def test_symlink_file(self):
        (self.root/'link.wav').symlink_to(self.root/'cue.wav');self.row['path']='link.wav'
        with self.assertRaisesRegex(AudioError,'SYMLINK'):self.read()
    def test_symlink_parent(self):
        (self.root/'assets').symlink_to(self.root,target_is_directory=True);self.row['path']='assets/cue.wav'
        with self.assertRaises(AudioError):self.read()
    def test_stale_timeline(self):
        self.raw['timeline_fingerprint']=fingerprint('stale')
        with self.assertRaisesRegex(AudioError,'STALE'):self.read()
    def test_stale_plan(self):
        self.raw['plan_fingerprint']=fingerprint('stale')
        with self.assertRaisesRegex(AudioError,'STALE'):self.read()
    def test_undeclared_fields(self):
        self.row['verified']=True
        with self.assertRaises(AudioError):self.read()
    def test_wrong_decoded_format(self):
        self.row['sample_rate']=48000
        with self.assertRaises(AudioError):self.read()
    def test_malformed_media(self):
        data=b'not wav';(self.root/'cue.wav').write_bytes(data);self.row['sha256']=hashlib.sha256(data).hexdigest()
        with self.assertRaises(AudioError):self.read()
    def test_missing_source_and_rights(self):
        for field,val in (('rights_ref',''),('source_refs',[])):
            row=dict(self.row);row[field]=val
            with self.assertRaises(AudioError):read_mix_spec(spec(self.sync,(row,)),self.root,self.sync)
    def test_publish_source_master_captions_and_hashes(self):
        out=self.root/'ready';index=publish_mix(self.result,out,sync=self.sync)
        self.assertEqual((out/'source.wav').read_bytes(),self.sync.wav_bytes)
        self.assertEqual((out/'master.wav').read_bytes(),self.result.wav_bytes)
        self.assertIn('captions.vtt',index)
        for name,item in index.items():self.assertEqual(hashlib.sha256((out/name).read_bytes()).hexdigest(),item['sha256'])
    def test_existing_output_not_overwritten(self):
        out=self.root/'ready';out.mkdir();(out/'sentinel').write_text('original')
        with self.assertRaisesRegex(AudioError,'EXISTS'):publish_mix(self.result,out)
        self.assertEqual((out/'sentinel').read_text(),'original')
    def test_output_symlink_rejected(self):
        out=self.root/'sym';out.symlink_to(self.root/'missing')
        with self.assertRaises(AudioError):publish_mix(self.result,out)
    def test_wrong_source_never_published(self):
        out=self.root/'wrong'
        with self.assertRaisesRegex(AudioError,'SOURCE_MISMATCH'):publish_mix(self.result,out,sync=real_sync('hindi'))
        self.assertFalse(out.exists())
    def test_review_needs_explicit_opt_in(self):
        result=mix_synchronized(self.sync,policy=MixPolicy(loudness=LoudnessPolicy(target_lufs=-10,max_boost_db=0)))
        self.assertTrue(result.receipt()['requires_review'])
        with self.assertRaisesRegex(AudioError,'REVIEW_REQUIRED'):publish_mix(result,self.root/'no')
        publish_mix(result,self.root/'review',allow_review=True)
        self.assertFalse(json.loads((self.root/'review/MIX_RECEIPT.json').read_text())['product_accepted'])
    def test_invalid_copy_path(self):
        with self.assertRaises(AudioError):publish_mix(self.result,self.root/'no',inputs={'../evil':b'bad'})
        self.assertFalse((self.root/'no').exists())
    def test_rehashed_unbound_caption_text_publication_blocked(self):
        from .test_audio_batch004_integration import reseal
        clock=self.result.clock();clock['captions'][0]['text']='X'*len(clock['captions'][0]['text']);clock['captions'][0]['lines']=[clock['captions'][0]['text']]
        with self.assertRaisesRegex(AudioError,'DERIVED_CLOCK'):publish_mix(reseal(self.result,clock=clock),self.root/'no',sync=self.sync)
        self.assertFalse((self.root/'no').exists())
    def test_cli_real_speech_and_spec_to_master(self):
        path=self.root/'mix.json';path.write_text(json.dumps(self.raw));out=self.root/'cli'
        argv=[sys.executable,'-B',str(ROOT/'scripts/audio_mix.py'),str(ROOT/'examples/audio_batch003/scene_animation_pause.json'),
              '--mix-spec',str(path),'--sync-spec',str(ROOT/'examples/audio_batch003/scene_animation_pause.spec.json'),
              '--output',str(out),'--cache',str(self.root/'cache'),'--cache-namespace','batch004-cli',
              '--allow-technical-voice','--standalone-fixture']
        p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,timeout=60)
        self.assertEqual(p.returncode,0,p.stderr);self.assertTrue((out/'master.wav').is_file())
        c=json.loads((out/'MIX_CLOCK.json').read_text());self.assertEqual(len(c['animations']),1)
        self.assertTrue((out/'inputs/sync.json').is_file())
    def test_cli_malformed_spec_blocked(self):
        path=self.root/'mix.json';path.write_text('{"bad":true}')
        p=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_mix.py'),str(ROOT/'examples/audio_batch003/scene_animation_pause.json'),
            '--mix-spec',str(path),'--output',str(self.root/'no'),'--cache',str(self.root/'cache'),'--cache-namespace','bad',
            '--allow-technical-voice','--standalone-fixture'],cwd=ROOT,capture_output=True,text=True,timeout=60)
        self.assertEqual(p.returncode,2);self.assertFalse((self.root/'no').exists())
    def test_cli_requires_technical_voice_opt_in(self):
        path=self.root/'mix.json';path.write_text(json.dumps(self.raw))
        p=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_mix.py'),str(ROOT/'examples/audio_batch003/scene_animation_pause.json'),
            '--mix-spec',str(path),'--output',str(self.root/'no'),'--cache',str(self.root/'cache'),'--cache-namespace','optin',
            '--standalone-fixture'],cwd=ROOT,capture_output=True,text=True,timeout=60)
        self.assertEqual(p.returncode,2);self.assertIn('TECHNICAL_VOICE_OPT_IN_REQUIRED',p.stderr);self.assertFalse((self.root/'no').exists())
