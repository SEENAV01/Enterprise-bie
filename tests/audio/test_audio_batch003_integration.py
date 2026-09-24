from pathlib import Path
from dataclasses import replace
from threading import Event
import json,os,re,subprocess,sys,tempfile,unittest,hashlib
from bie.audio.common import AudioError,fingerprint
from bie.audio.caption_alignment import align_captions
from bie.audio.dir_sync_adapter import to_dir_timing
from bie.director.script_plan import ScriptSegment,build_script_plan
from bie.director.voiceover_generation import generate_voiceover
from bie.director.speech_timing import utterances_from_script
from tests.audio.sync_test_support import fixture
ROOT=Path(__file__).resolve().parents[2]

class SyncIntegration(unittest.TestCase):
    def run_cli(self,output,*,example='english',profile='batch001-144',extra=(),cache=None):
        argv=[sys.executable,str(ROOT/'scripts/audio_sync.py'),str(ROOT/f'examples/audio_batch002/{example}.json'),
              '--output',str(output),'--profile',profile,'--cache',str(cache or output.parent/'cache'),'--cache-namespace','integration',
              '--allow-technical-voice','--standalone-fixture',*extra]
        return subprocess.run(argv,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=60)
    def test_english_cli_exact_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'english';p=self.run_cli(out);self.assertEqual(p.returncode,0,p.stderr)
            report=json.loads((out/'SYNC_REPORT.json').read_text());self.assertTrue(report['scene_clock_verified']);self.assertFalse(report['product_accepted'])
            h=json.loads((out/'OUTPUT_SHA256.json').read_text());self.assertEqual(set(h),{p.name for p in out.iterdir()}-{'OUTPUT_SHA256.json'})
            for name,value in h.items():self.assertEqual(hashlib.sha256((out/name).read_bytes()).hexdigest(),value)
            self.assertIn('\\frac',report['plan']['segments'][0]['display_text'])
    def test_hindi_cli_unicode_captions(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'hi';p=self.run_cli(out,example='hindi');self.assertEqual(p.returncode,0,p.stderr)
            self.assertTrue(any('\u0900'<=c<='\u097f' for c in (out/'captions.vtt').read_text()))
    def test_compat204_sum_reading_retained(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'compat';p=self.run_cli(out,example='compat204',profile='batch001-204');self.assertEqual(p.returncode,0,p.stderr)
            report=json.loads((out/'SYNC_REPORT.json').read_text());self.assertEqual(report['plan']['profile'],'batch001-204')
            self.assertIn('sum',' '.join(w['spoken'] for t in report['word_timings'] for w in t['words']))
    def test_mixed_language_native_timing(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'mixed';p=self.run_cli(out,example='mixed',extra=('--language-terms',str(ROOT/'examples/audio_batch002/mixed_terms.json')))
            self.assertEqual(p.returncode,0,p.stderr);r=json.loads((out/'WORD_TIMINGS.json').read_text())
            self.assertIn('photosynthesis',[w['spoken'] for s in r['segments'] for w in s['words']])
    def test_cache_keeps_media_but_timing_replay_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'a';b=Path(td)/'b';one=self.run_cli(a);two=self.run_cli(b)
            self.assertEqual(one.returncode,0,one.stderr);self.assertEqual(two.returncode,0,two.stderr)
            self.assertEqual((a/'speech.wav').read_bytes(),(b/'speech.wav').read_bytes());self.assertEqual((a/'WORD_TIMINGS.json').read_bytes(),(b/'WORD_TIMINGS.json').read_bytes())
            summary=json.loads(two.stdout);self.assertEqual(summary['tts_generation_calls'],0);self.assertGreater(summary['native_synthesis_calls_including_replay'],0)
    def test_review_cannot_publish(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'no';p=self.run_cli(out,example='review_required');self.assertEqual(p.returncode,2);self.assertFalse(out.exists())
    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'keep';out.mkdir();(out/'sentinel').write_text('original');p=self.run_cli(out)
            self.assertEqual(p.returncode,2);self.assertEqual((out/'sentinel').read_text(),'original')
    def test_stale_animation_spec_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            spec=Path(td)/'spec.json';spec.write_text(json.dumps({'schema_version':'bie.audio.word-anchor-input/1','plan_fingerprint':fingerprint('wrong'),'bindings':[]}))
            out=Path(td)/'no';p=self.run_cli(out,extra=('--sync-spec',str(spec)));self.assertEqual(p.returncode,2);self.assertFalse(out.exists());self.assertIn('SOURCE_CHANGED',p.stderr)
    def test_real_upstream_dir_alignment_adapter(self):
        p,a,t=fixture(('Alpha beta gamma.',));s=p.segments[0]
        script=build_script_plan('synthetic:sync',(ScriptSegment('u0','scene:0','EXPLAIN','explain relation',('source:p1',),('objective:test',)),),'voice:teacher')
        d=generate_voiceover('u0',('Alpha beta gamma.',),{'Alpha beta gamma.':('source:p1',)})
        u=tuple(utterances_from_script(script,(d,),('u0',),'en'))[0]
        result=to_dir_timing(u,a[0],t[0],require_measured=False)
        self.assertEqual(len(result.utterances[0].words),3);self.assertFalse(result.audio_verified);self.assertEqual(result.basis,'REPORTED_AUDIO_ALIGNMENT')
    def test_dir_revision_mismatch_rejected(self):
        p,a,t=fixture();from tests.audio.audio_test_support import utterance
        with self.assertRaisesRegex(AudioError,'EXACT_UTTERANCE'):to_dir_timing(utterance('Different text.'),a[0],t[0],require_measured=False)
    def test_no_remote_write_or_render_claim(self):
        code=(ROOT/'scripts/audio_sync.py').read_text();self.assertNotIn('GitHub.',code);self.assertNotIn('git push',code)
    def test_native_backend_missing_does_not_skip(self):
        from bie.audio.timed_espeak_provider import TimedEspeakProvider
        with self.assertRaises((OSError,ValueError)):TimedEspeakProvider('/does-not-exist/espeak')

    def test_multiscene_actual_media_pause_and_animation_hold(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'multi'
            argv=[sys.executable,str(ROOT/'scripts/audio_sync.py'),str(ROOT/'examples/audio_batch003/scene_animation_pause.json'),
                '--sync-spec',str(ROOT/'examples/audio_batch003/scene_animation_pause.spec.json'),'--output',str(out),
                '--cache',str(Path(td)/'cache'),'--cache-namespace','multiscene','--standalone-fixture','--allow-technical-voice']
            run=subprocess.run(argv,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=60)
            self.assertEqual(run.returncode,0,run.stderr)
            r=json.loads((out/'SYNC_REPORT.json').read_text());a=json.loads((out/'ANIMATION_SYNC.json').read_text())
            self.assertEqual(len(r['timeline']['scenes']),2);self.assertEqual(len(r['pause_sync']['windows']),2)
            self.assertEqual(len(a['tracks']),1);keys=a['sample_keyframes']['trace:1']
            self.assertEqual(keys[1][1:],keys[2][1:]);self.assertLess(keys[1][0],keys[2][0])
            self.assertFalse(a['rendered']);self.assertFalse(r['acoustic_alignment_verified'])
