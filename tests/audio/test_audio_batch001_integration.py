import unittest,subprocess,sys,os,json,tempfile
from dataclasses import replace,asdict
from pathlib import Path
from bie.audio.preparation import *
from bie.audio.lexicon import build_lexicon,Lexeme,export_pls
from bie.audio.acronym_pronunciation import make_acronyms,AcronymRule
from bie.audio.symbol_pronunciation import make_table,SymbolRule
from bie.audio.common import AudioError,strict_json
from tests.audio.audio_test_support import utterance,empty_options,director

class PreparationIntegrationTests(unittest.TestCase):
    def test_dir_to_preparation(self):
        s,d,o,us=director('Coulomb explains \\(x^2+2\\). DNA stays unchanged.')
        opts=empty_options();opts['lexicon']=build_lexicon('v',(Lexeme('c','Coulomb','en','koo lom',('lex:p1',)),));opts['acronyms']=make_acronyms('v',(AcronymRule('DNA','en','LETTERS',('lex:p1',)),))
        p=prepare_narration(us,**opts);self.assertTrue(p.preparation_passed);self.assertEqual(p.spoken_segments[0].display_text,d[0].text);self.assertIn('koo lom explains x squared plus two',p.spoken_segments[0].synthesis_text);self.assertIn('dee en ay',p.spoken_segments[0].synthesis_text)
    def test_hindi_math_and_initialism(self):
        u=utterance('AI में \\(x^2+2\\) पढ़ें।','hi');opts=empty_options('hi');opts['acronyms']=make_acronyms('v',(AcronymRule('AI','hi','LETTERS',('e',)),))
        p=prepare_narration((u,),**opts);self.assertTrue(p.preparation_passed);self.assertIn('ए आई',p.spoken_segments[0].synthesis_text);self.assertIn('एक्स का वर्ग',p.spoken_segments[0].synthesis_text)
    def test_unknown_acronym_review_not_fake_pass(self):
        p=prepare_narration((utterance('XYZ works.'),),**empty_options());self.assertFalse(p.preparation_passed);self.assertIn('XYZ',p.spoken_segments[0].synthesis_text)
    def test_plain_numeric_needs_owned_reading(self):
        p=prepare_narration((utterance('The value is 2.50.'),),**empty_options());self.assertFalse(p.preparation_passed)
    def test_numeric_explicit_realization(self):
        u=utterance('Value 2.50.');r=ReadingRequest('s1',u.fingerprint(),6,10,'2.50','MATH')
        p=prepare_narration((u,),requests=(r,),**empty_options());self.assertTrue(p.preparation_passed);self.assertIn('two point five zero',p.spoken_segments[0].synthesis_text)
    def test_ambiguous_symbol_review(self):
        p=prepare_narration((utterance('Read µ carefully.'),),**empty_options());self.assertFalse(p.preparation_passed)
    def test_symbol_explicit_sense(self):
        u=utterance('Use µ here.');opts=empty_options();opts['symbols']=make_table('v',(SymbolRule('µ','en','coefficient','mu',('e',)),))
        p=prepare_narration((u,),requests=(ReadingRequest('s1',u.fingerprint(),4,5,'µ','SYMBOL','coefficient'),),**opts);self.assertTrue(p.preparation_passed);self.assertIn('mu',p.spoken_segments[0].synthesis_text)
    def test_old_request_on_edited_voice_rejected(self):
        u=utterance('Read x.');r=ReadingRequest('s1',u.fingerprint(),5,6,'x','MATH')
        with self.assertRaisesRegex(AudioError,'STALE'):prepare_narration((replace(u,voice_id='other'),),requests=(r,),**empty_options())
    def test_unbalanced_marker_not_discarded(self):
        with self.assertRaisesRegex(AudioError,'UNBALANCED'):prepare_narration((utterance(r'Read \(x.'),),**empty_options())
    def test_protected_math_provider_limit(self):
        u=utterance(r'Read \(a + b + c + d\).')
        with self.assertRaisesRegex(AudioError,'INDIVISIBLE'):prepare_narration((u,),policy=SegmentPolicy(max_chars=10,max_utf8_bytes=40),**empty_options())
    def test_phoneme_requirement_kept(self):
        opts=empty_options();opts['lexicon']=build_lexicon('v',(Lexeme('p','Coulomb','en','kuːlɒm',('e',),mode='PHONEME',alphabet='ipa'),))
        p=prepare_narration((utterance('Coulomb explains.'),),**opts);self.assertEqual(p.spoken_segments[0].provider_requirements,('phoneme:ipa',));self.assertFalse(p.tts_request_ready)
    def test_pause_text_pronunciation_independent(self):
        u=utterance('DNA. Then move.');opts=empty_options();opts['acronyms']=make_acronyms('v',(AcronymRule('DNA','en','LETTERS',('e',)),))
        p=prepare_narration((u,),pauses=(Pause('s1',4,1200,('dir:pause',)),),**opts)
        self.assertEqual(p.segmentation.segments[0].pause_after_ms,1200);self.assertEqual(p.spoken_segments[0].synthesis_text,'dee en ay.')
    def test_no_markup_execution_or_audio_receipt(self):
        u=utterance('Text <break time="9s"/> only.');p=prepare_narration((u,),**empty_options())
        self.assertEqual(p.spoken_segments[0].synthesis_text,u.text);self.assertFalse(p.audio_generated);self.assertFalse(p.audio_verified);self.assertFalse(p.product_accepted)
    def test_input_review_cannot_be_cleared(self):
        u=replace(utterance(),review_reasons=('UNSUPPORTED_CLAIMS_WITHHELD',));p=prepare_narration((u,),**empty_options());self.assertFalse(p.preparation_passed)
    def test_revalidation_dictionary_revision(self):
        u=utterance();opts=empty_options();p=prepare_narration((u,),**opts);opts['lexicon']=build_lexicon('new',())
        with self.assertRaisesRegex(AudioError,'STALE_OR_EDITED'):validate_preparation(p,(u,),**opts)
    def test_revalidation_detects_spoken_edit(self):
        u=utterance();opts=empty_options();p=prepare_narration((u,),**opts)
        bad=replace(p,spoken_segments=(replace(p.spoken_segments[0],synthesis_text='wrong'),))
        with self.assertRaises(AudioError):validate_preparation(bad,(u,),**opts)
    def test_overlapping_explicit_auto_reading(self):
        u=utterance(r'Read \(x+2\).');r=ReadingRequest('s1',u.fingerprint(),7,8,'x','MATH')
        with self.assertRaisesRegex(AudioError,'CONFLICTING'):prepare_narration((u,),requests=(r,),**empty_options())
    def test_invalid_request_type_controlled(self):
        with self.assertRaises(AudioError):prepare_narration((utterance(),),requests=('bad',),**empty_options())
    def test_strict_json_duplicate_and_nonfinite(self):
        for s in ('{"x":1,"x":2}','{"x":NaN}','{"x":1e999}'):
            with self.subTest(s=s),self.assertRaises(AudioError):strict_json(s)
    def test_fingerprint_across_clean_processes(self):
        code="from tests.audio.audio_test_support import utterance,empty_options;from bie.audio.preparation import prepare_narration;print(prepare_narration((utterance(),),**empty_options()).fingerprint())"
        values=[]
        for seed in ('1','9','333'):
            env=dict(os.environ,PYTHONHASHSEED=seed);p=subprocess.run([sys.executable,'-B','-c',code],env=env,capture_output=True,text=True,check=True);values.append(p.stdout)
        self.assertEqual(len(set(values)),1)

class BoundaryRegressionTests(unittest.TestCase):
    def test_unknown_request_with_inline_math(self):
        with self.assertRaises(AudioError):prepare_narration((utterance(r'Read \(x\).'),),requests=('bad',),**empty_options())
    def test_expansion_cannot_exceed_request_limit_unnoticed(self):
        u=utterance('AI here.');opts=empty_options();opts['acronyms']=make_acronyms('v',(AcronymRule('AI','en','EXPANSION',('e',),'artificial intelligence'),))
        p=prepare_narration((u,),policy=SegmentPolicy(max_chars=10,max_utf8_bytes=40),**opts)
        self.assertFalse(p.preparation_passed);self.assertTrue(any('EXCEEDS_REQUEST_LIMIT' in r for r in p.review_reasons))
    def test_ascii_relations_supported(self):
        from bie.audio.math_pronunciation import pronounce_math
        self.assertEqual(pronounce_math('x<=2').reading.spoken,pronounce_math('x≤2').reading.spoken)
        self.assertEqual(pronounce_math('x!=2').reading.spoken,pronounce_math('x≠2').reading.spoken)
    def test_hindi_relation_direction(self):
        from bie.audio.math_pronunciation import pronounce_math
        self.assertEqual(pronounce_math('x<2','hi').reading.spoken,'एक्स, दो से छोटा है')
    def test_budget_never_discards_lesson_tail(self):
        u=utterance(('This is a complete sentence. '*2000)+'Last required sentence.')
        p=split_narration((u,),policy=SegmentPolicy(max_chars=200,max_utf8_bytes=800))
        self.assertEqual(''.join(s.display_text for s in p.segments),u.text);self.assertTrue(p.segments[-1].display_text.endswith('Last required sentence.'))
    def test_emoji_symbol_not_implicitly_speech_verified(self):
        p=prepare_narration((utterance('Notice the ⚡ mark.'),),**empty_options());self.assertFalse(p.preparation_passed)

class CommandLineContracts(unittest.TestCase):
    def invoke(self,name,output):
        root=Path(__file__).resolve().parents[2]
        return subprocess.run([sys.executable,'-B',str(root/'scripts/audio_prepare.py'),'--standalone-fixture',str(root/'examples/audio'/name),'--output',str(output)],capture_output=True,text=True,timeout=15)
    def test_cli_english(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'plan.json';r=self.invoke('english.json',out);self.assertEqual(r.returncode,0,r.stderr);p=json.loads(out.read_text());self.assertTrue(p['preparation_passed']);self.assertFalse(p['audio_generated'])
    def test_cli_hindi(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'plan.json';r=self.invoke('hindi.json',out);self.assertEqual(r.returncode,0,r.stderr);self.assertIn('ए आई',out.read_text())
    def test_cli_review_exit_two_with_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'plan.json';r=self.invoke('needs_review.json',out);self.assertEqual(r.returncode,2);p=json.loads(out.read_text());self.assertFalse(p['preparation_passed']);self.assertIn('XYZ',p['spoken_segments'][0]['display_text'])
    def test_cli_never_overwrites_existing_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'plan.json';out.write_bytes(b'keep exact');r=self.invoke('english.json',out);self.assertEqual(r.returncode,2);self.assertEqual(out.read_bytes(),b'keep exact')
    def test_pinned_upstream_blob_identity(self):
        import hashlib
        root=Path(__file__).resolve().parents[2];m=json.loads((root/'docs/evidence/audio-integration-001/CANONICAL_DEPENDENCY_BINDING.json').read_text())
        rows=[x for x in m['files'] if x['group']=='dir_inherited'];self.assertEqual(len(rows),5)
        for item in rows:
            b=(root/item['path']).read_bytes();self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),item['expected_git_blob'])
    def test_production_modules_do_not_import_archival_snapshot(self):
        root=Path(__file__).resolve().parents[2]
        for p in (root/'bie/audio').glob('*.py'):
            s=p.read_text();self.assertNotIn('dependency_snapshot',s);self.assertNotIn('sys.path',s)
    def test_bad_input_does_not_publish(self):
        root=Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'bad.json';source.write_text('{"schema_version":"bad"}');out=Path(d)/'result.json'
            r=subprocess.run([sys.executable,'-B',str(root/'scripts/audio_prepare.py'),'--standalone-fixture',str(source),'--output',str(out)],capture_output=True,text=True)
            self.assertEqual(r.returncode,2);self.assertFalse(out.exists());self.assertFalse(list(Path(d).glob('.audio-preparation-*')))
    def test_source_evidence_unchanged_by_preparation(self):
        u=utterance(r'Read \(x^2\).');before=u.fingerprint();p=prepare_narration((u,),**empty_options())
        self.assertEqual(before,u.fingerprint());self.assertEqual(p.segmentation.segments[0].evidence_ids,u.evidence_ids)
