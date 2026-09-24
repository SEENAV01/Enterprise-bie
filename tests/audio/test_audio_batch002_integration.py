from pathlib import Path
from dataclasses import replace
import json,os,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[2]

class EndToEndCLI(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def invoke(self,name='english',output='result',*,technical=True,extra=()):
        argv=[sys.executable,'-B',str(ROOT/'scripts/audio_synthesize.py'),str(ROOT/'examples/audio_batch002'/f'{name}.json'),
            '--output',str(self.root/output),'--cache',str(self.root/'cache'),'--cache-namespace','integration-test','--standalone-fixture']
        if technical:argv.append('--allow-technical-voice')
        return subprocess.run([*argv,*extra],cwd=ROOT,capture_output=True,text=True,timeout=30)
    def test_actual_end_to_end_speech_from_canonical_dir(self):
        r=self.invoke();self.assertEqual(r.returncode,0,r.stderr);report=json.loads((self.root/'result/SYNTHESIS_REPORT.json').read_text())
        self.assertTrue(report['audio_generated']);self.assertFalse(report['product_accepted']);self.assertTrue((self.root/'result/speech.wav').is_file())
    def test_original204_preparation_to_actual_speech(self):
        r=self.invoke('compat204',extra=('--profile','batch001-204'));self.assertEqual(r.returncode,0,r.stderr)
        report=json.loads((self.root/'result/SYNTHESIS_REPORT.json').read_text());self.assertEqual(report['profile'],'batch001-204')
    def test_cinematic_not_implicitly_substituted(self):
        r=self.invoke(technical=False);self.assertEqual(r.returncode,2);self.assertIn('PRODUCTION_VOICE_NOT_CONFIGURED',r.stderr);self.assertFalse((self.root/'result').exists())
    def test_review_not_synthesized(self):
        r=self.invoke('review_required');self.assertEqual(r.returncode,2);self.assertFalse((self.root/'result').exists())
    def test_cli_cache_hit(self):
        a=self.invoke(output='one');b=self.invoke(output='two');self.assertEqual(a.returncode,0,a.stderr);self.assertEqual(b.returncode,0,b.stderr)
        r=json.loads(b.stdout);self.assertEqual(r['provider_invocations'],0);self.assertGreater(r['cache_hits'],0)
    def test_destination_not_overwritten(self):
        (self.root/'result').mkdir();(self.root/'result/user-file').write_text('retained');r=self.invoke()
        self.assertEqual(r.returncode,2);self.assertEqual((self.root/'result/user-file').read_text(),'retained')
    def test_symlink_destination_not_followed(self):
        (self.root/'target').mkdir();(self.root/'result').symlink_to(self.root/'target',target_is_directory=True);r=self.invoke()
        self.assertEqual(r.returncode,2);self.assertEqual(list((self.root/'target').iterdir()),[])
    def test_pause_sample_metadata_measured(self):
        r=self.invoke();self.assertEqual(r.returncode,0,r.stderr);p=json.loads((self.root/'result/SYNTHESIS_REPORT.json').read_text())
        self.assertEqual(p['segments'][-1]['receipt']['requested_pause_samples'],8820)
        self.assertEqual(p['segments'][-1]['end_sample'],p['assembled_media']['samples_per_channel']);self.assertFalse(p['word_alignment_verified'])
    def test_source_text_never_overwritten(self):
        r=self.invoke();self.assertEqual(r.returncode,0,r.stderr);source=json.loads((ROOT/'examples/audio_batch002/english.json').read_text())
        report=json.loads((self.root/'result/SYNTHESIS_REPORT.json').read_text());self.assertEqual(''.join(s['display_text'] for s in report['plan']['segments']),source['drafts'][0]['text'])
    def test_mixed_language_cli(self):
        r=self.invoke('mixed',extra=('--language-terms',str(ROOT/'examples/audio_batch002/mixed_terms.json')));self.assertEqual(r.returncode,0,r.stderr)
        p=json.loads((self.root/'result/SYNTHESIS_REPORT.json').read_text());languages={x['language'] for s in p['plan']['segments'] for x in s['spans']};self.assertEqual(languages,{'en','hi'})
