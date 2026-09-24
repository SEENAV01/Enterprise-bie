from dataclasses import replace,asdict
from pathlib import Path
import json, os, subprocess, sys, tempfile, unittest, hashlib
from bie.audio.compat204.contracts import *
from bie.audio.compat204.narration_segmentation import *
from bie.audio.compat204.pronunciation_lexicon import *
from bie.audio.compat204.voiceover_preparation import *
from tests.audio.compat204_support import document, block, rule, annotation

ROOT=Path(__file__).resolve().parents[2]

class PreparationIntegrationTests(unittest.TestCase):
    def test_full_plain_math_term_symbol_acronym(self):
        raw='Coulomb explains $F=ma$. DNA uses μ as a symbol.'
        d=document(raw,annotations=(annotation(raw,'μ','symbol',role='greek_name'),))
        l=Lexicon('l','1',(rule(),rule('Coulomb','term','alias','koo lom')))
        p=prepare_voiceover(d,l)
        self.assertEqual(p.status,'PRONUNCIATION_PREPARED_NO_AUDIO')
        self.assertEqual(p.segments[0].spoken_text,'koo lom explains capital f equals m times a. dee en ay uses mu as a symbol.')
        self.assertEqual(p.segments[0].original_text,raw)
        verify_preparation(p,d,l)
    def test_source_map_covers_every_character(self):
        raw='  DNA and $x^2$.\nNext. '
        d=document(raw);l=Lexicon('l','1',(rule(),));p=prepare_voiceover(d,l,SegmentationPolicy(20,200))
        for segment in p.segments:
            self.assertEqual(''.join(x.original_text for x in segment.pieces),segment.original_text)
            for x in segment.pieces:self.assertEqual(raw[x.start_char:x.end_char],x.original_text)
        self.assertEqual(''.join(s.original_text for s in p.segments),raw)
    def test_phrase_not_cut_between_segments(self):
        d=document('Prefix. New Delhi University teaches. End.')
        l=Lexicon('l','1',(rule('New Delhi University','term','alias','new delhi university'),))
        p=prepare_voiceover(d,l,SegmentationPolicy(28,200))
        self.assertTrue(any(x.original_text=='New Delhi University' for s in p.segments for x in s.pieces))
    def test_unknown_acronym_review_not_expanded(self):
        p=prepare_voiceover(document('Read XYZ.'),Lexicon('l','1'))
        self.assertEqual(p.status,'REVIEW_REQUIRED');self.assertIn('XYZ',p.segments[0].spoken_text)
    def test_unsupported_math_review_not_simplified(self):
        p=prepare_voiceover(document(r'Read $\input{x}$.'),Lexicon('l','1'))
        self.assertTrue(p.requires_review);self.assertIn(r'$\input{x}$',p.segments[0].spoken_text)
    def test_ambiguous_greek_review_not_guessed(self):
        p=prepare_voiceover(document('Read μ.'),Lexicon('l','1'))
        self.assertEqual(p.issues[0].code,'SYMBOL_ROLE_REQUIRED')
    def test_numerical_date_not_invented(self):
        p=prepare_voiceover(document('On 01/05/1991.'),Lexicon('l','1'))
        self.assertTrue(p.requires_review);self.assertEqual(p.segments[0].spoken_text,'On 01/05/1991.')
    def test_non_recursive_replacement(self):
        d=document('alpha');l=Lexicon('l','1',(rule('alpha','term','alias','beta'),rule('beta','term','alias','gamma')))
        self.assertEqual(prepare_voiceover(d,l).segments[0].spoken_text,'beta')
    def test_markup_like_source_is_data(self):
        raw='<script>not executable</script>'
        d=document(raw,annotations=(annotation(raw,raw,'verbatim'),))
        p=prepare_voiceover(d,Lexicon('l','1'));self.assertEqual(p.segments[0].spoken_text,raw)
    def test_unknown_caps_can_be_explicit_verbatim(self):
        raw='STOP here.';d=document(raw,annotations=(annotation(raw,'STOP','verbatim'),))
        self.assertFalse(prepare_voiceover(d,Lexicon('l','1')).requires_review)
    def test_review_propagation(self):
        p=prepare_voiceover(document(review_reasons=('UNSUPPORTED_CLAIMS_WITHHELD',)),Lexicon('l','1'))
        self.assertEqual(p.issues[0].code,'UPSTREAM_REVIEW');self.assertEqual(p.issues[0].owner_task,'DIR')
    def test_original_unicode_unchanged(self):
        raw='नमस्ते। यह विज्ञान है।';d=document(raw,language='hi')
        p=prepare_voiceover(d,Lexicon('l','1'));self.assertEqual(p.segments[0].original_text,raw);self.assertTrue(p.requires_review)
    def test_exact_lexicon_unicode_realization(self):
        d=document('DNA',language='hi');l=Lexicon('l','1',(rule('DNA',mode='word',spoken='डी एन ए',language='hi'),))
        p=prepare_voiceover(d,l);self.assertEqual(p.segments[0].spoken_text,'डी एन ए');self.assertTrue(p.requires_review)
    def test_changed_source_invalidates_plan(self):
        d=document();l=Lexicon('l','1');p=prepare_voiceover(d,l)
        self.assertRaisesRegex(AudioError,'MISMATCH',verify_preparation,p,document('Different.'),l)
    def test_changed_lexicon_invalidates_plan(self):
        d=document('DNA');l=Lexicon('l','1',(rule(),));p=prepare_voiceover(d,l)
        self.assertRaisesRegex(AudioError,'MISMATCH',verify_preparation,p,d,replace(l,version='2'))
    def test_edited_speech_rejected(self):
        d=document();l=Lexicon('l','1');p=prepare_voiceover(d,l)
        p=replace(p,segments=(replace(p.segments[0],spoken_text='changed'),))
        self.assertRaisesRegex(AudioError,'MISMATCH',verify_preparation,p,d,l)
    def test_cleared_review_rejected(self):
        d=document('XYZ');l=Lexicon('l','1');p=replace(prepare_voiceover(d,l),issues=())
        self.assertRaisesRegex(AudioError,'MISMATCH',verify_preparation,p,d,l)
    def test_acceptance_flag_rejected(self):
        d=document();l=Lexicon('l','1');p=replace(prepare_voiceover(d,l),product_accepted=True)
        self.assertRaisesRegex(AudioError,'MISMATCH',verify_preparation,p,d,l)
    def test_numeric_false_not_bool_rejected(self):
        d=document();l=Lexicon('l','1');p=replace(prepare_voiceover(d,l),audio_generated=0)
        self.assertRaisesRegex(AudioError,'MISMATCH',verify_preparation,p,d,l)
    def test_expected_document_checked(self):
        self.assertRaisesRegex(AudioError,'STALE_DOCUMENT',prepare_voiceover,document(),Lexicon('l','1'),expected_document=fingerprint('other'))
    def test_expected_lexicon_checked(self):
        self.assertRaisesRegex(AudioError,'STALE_LEXICON',prepare_voiceover,document(),Lexicon('l','1'),expected_lexicon=fingerprint('other'))
    def test_all_source_objective_bindings_preserved(self):
        d=document('DNA');p=prepare_voiceover(d,Lexicon('l','1',(rule(),)))
        self.assertEqual(p.segments[0].objective_ids,d.blocks[0].objective_ids)
        self.assertTrue(all(set(d.blocks[0].evidence_ids)<=set(x.source_refs) for x in p.segments[0].pieces))
    def test_speech_has_no_fabricated_timestamps(self):
        p=prepare_voiceover(document(),Lexicon('l','1'));raw=p.to_dict()
        self.assertFalse(raw['audio_generated']);self.assertFalse(raw['audio_alignment_verified']);self.assertNotIn('duration_ms',raw)
    def test_boundary_with_literal_currency(self):
        raw='Price $5.';d=document(raw,annotations=(annotation(raw,'$5','verbatim'),))
        self.assertFalse(prepare_voiceover(d,Lexicon('l','1')).requires_review)
    def test_rule_mismatch_surfaces_as_review(self):
        raw='DNA';d=document(raw,annotations=(annotation(raw,'DNA','acronym',rule_id='no-such-rule'),))
        p=prepare_voiceover(d,Lexicon('l','1',(rule(),)))
        self.assertTrue(p.requires_review);self.assertEqual(p.issues[0].code,'EXPLICIT_RULE_MISMATCH')
    def test_empty_or_all_whitespace_not_audio(self):
        self.assertRaises(AudioError,prepare_voiceover,document('   '),Lexicon('l','1'))
    def test_many_blocks_no_loss(self):
        blocks=tuple(block('Narration remains intact. ',block_id=f'u{i}',segment_id=f'g{i}') for i in range(100))
        d=replace(document(),blocks=blocks);p=prepare_voiceover(d,Lexicon('l','1'))
        self.assertEqual(len(p.segments),100);self.assertEqual([s.block_id for s in p.segments],[b.block_id for b in blocks])
    def test_large_block_segmenter_budget(self):
        raw='word '*10000;d=document(raw);p=segment_narration(d,SegmentationPolicy(64,256))
        verify_segments(p,d);self.assertEqual(''.join(x.raw_text for x in p.segments),raw)

    def test_unknown_math_symbol_does_not_silently_pass(self):
        p=prepare_voiceover(document('Read ∫ here.'),Lexicon('l','1'))
        self.assertTrue(p.requires_review);self.assertIn('∫',p.segments[0].spoken_text)
    def test_superscript_outside_math_needs_reading(self):
        self.assertTrue(prepare_voiceover(document('Read x².'),Lexicon('l','1')).requires_review)
    def test_symbol_phoneme_not_dropped(self):
        raw='μ';d=document(raw,annotations=(annotation(raw,'μ','symbol',role='greek_name'),))
        l=Lexicon('l','1',(rule('μ','symbol','alias','mu',role='greek_name',phoneme='mjuː',alphabet='ipa'),))
        p=prepare_voiceover(d,l);self.assertEqual(p.segments[0].pieces[0].phoneme,'mjuː')

class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.request=self.root/'request.json';self.output=self.root/'out'
    def tearDown(self):self.tmp.cleanup()
    def write(self,raw='Read DNA.'):
        req={'document':asdict(document(raw)),'lexicon':asdict(Lexicon('l','1',(rule(),))),'policy':asdict(SegmentationPolicy())}
        self.request.write_text(json.dumps(req,ensure_ascii=False));return req
    def run_cli(self):
        return subprocess.run([sys.executable,'-B','-m','bie.audio.compat204',str(self.request),'--output',str(self.output)],cwd=ROOT,capture_output=True,text=True,timeout=20)
    def test_real_cli_success_no_audio(self):
        self.write();r=self.run_cli();self.assertEqual(r.returncode,0,r.stderr)
        obj=json.loads((self.output/'VOICEOVER_PREPARATION.json').read_text());self.assertFalse(obj['audio_generated']);self.assertEqual(obj['segments'][0]['spoken_text'],'Read dee en ay.')
    def test_cli_review_exit_two_keeps_evidence(self):
        self.write('XYZ.');r=self.run_cli();self.assertEqual(r.returncode,2);self.assertTrue((self.output/'VOICEOVER_PREPARATION.json').exists())
    def test_invalid_math_leaves_no_output(self):
        self.write('Read $unclosed');r=self.run_cli();self.assertEqual(r.returncode,2);self.assertFalse(self.output.exists())
    def test_existing_output_not_overwritten(self):
        self.write();self.output.mkdir();(self.output/'keep').write_text('old');r=self.run_cli();self.assertEqual(r.returncode,2);self.assertEqual((self.output/'keep').read_text(),'old')
    def test_duplicate_json_key_rejected(self):
        self.request.write_text('{"document": {}, "document": {}}');r=self.run_cli();self.assertIn('DUPLICATE_JSON_KEY',r.stderr);self.assertFalse(self.output.exists())
    def test_unknown_key_rejected(self):
        req=self.write();req['waive_review']=True;self.request.write_text(json.dumps(req));r=self.run_cli();self.assertIn('REQUEST_KEYS',r.stderr)
    def test_json_nan_rejected(self):
        self.request.write_text('{"x":NaN}');self.assertIn('NONFINITE_JSON',self.run_cli().stderr)
    def test_request_symlink_rejected(self):
        self.write();copy=self.root/'real.json';self.request.rename(copy);self.request.symlink_to(copy);self.assertIn('REQUEST_FILE_INVALID',self.run_cli().stderr)
    def test_output_parent_symlink_rejected(self):
        self.write();target=self.root/'real';target.mkdir();link=self.root/'link';link.symlink_to(target,target_is_directory=True);self.output=link/'out';self.assertIn('SYMLINK',self.run_cli().stderr)
    def test_all_output_hashes_match(self):
        self.write();r=self.run_cli();self.assertEqual(r.returncode,0,r.stderr)
        for name,expected in json.loads((self.output/'OUTPUT_SHA256.json').read_text()).items():self.assertEqual('sha256:'+hashlib.sha256((self.output/name).read_bytes()).hexdigest(),expected)
    def test_independent_processes_exact_output(self):
        self.write();r=self.run_cli();self.assertEqual(r.returncode,0,r.stderr);a=(self.output/'VOICEOVER_PREPARATION.json').read_bytes()
        self.output=self.root/'out2';r=self.run_cli();self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(a,(self.output/'VOICEOVER_PREPARATION.json').read_bytes())
    def test_spoken_preview_is_usable(self):
        self.write();self.run_cli();s=(self.output/'SPOKEN_PREVIEW.txt').read_text();self.assertIn('ORIGINAL: Read DNA.',s);self.assertIn('SPOKEN: Read dee en ay.',s)
