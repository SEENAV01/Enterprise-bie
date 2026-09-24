from dataclasses import asdict, replace, FrozenInstanceError
import json, unittest
from bie.audio.compat204.contracts import *
from bie.audio.compat204.narration_segmentation import *
from tests.audio.compat204_support import block, document, annotation

class SegmentationTests(unittest.TestCase):
    def test_roundtrip_all_whitespace(self):
        d=document('  First sentence.\r\n\r\nSecond\t sentence.  ')
        p=segment_narration(d,SegmentationPolicy(24,120))
        self.assertEqual(''.join(s.raw_text for s in p.segments),d.blocks[0].raw_text)
        verify_segments(p,d)
    def test_math_expression_is_not_split(self):
        d=document('First words. $x + y + z$. Then finish.')
        p=segment_narration(d,SegmentationPolicy(20,200))
        self.assertTrue(any('$x + y + z$' in s.raw_text for s in p.segments))
    def test_long_atomic_expression_blocks_without_loss(self):
        with self.assertRaisesRegex(AudioError,'UNSPLITTABLE'):
            segment_narration(document('$'+'x + '*20+'x$'),SegmentationPolicy(20,100))
    def test_annotations_protect_phrases(self):
        raw='Read New Delhi University exactly.'
        d=document(raw,annotations=(annotation(raw,'New Delhi University','term'),))
        p=segment_narration(d,SegmentationPolicy(26,200))
        self.assertTrue(any('New Delhi University' in s.raw_text for s in p.segments))
    def test_utf8_byte_budget(self):
        d=document('यह एक वाक्य है। यह दूसरा वाक्य है।')
        p=segment_narration(d,SegmentationPolicy(100,48))
        self.assertTrue(all(len(s.raw_text.encode())<=48 for s in p.segments))
        verify_segments(p,d)
    def test_hindi_marks_not_cut(self):
        d=document('क्षेत्र में विज्ञान है। नमस्ते मित्र।')
        p=segment_narration(d,SegmentationPolicy(16,64))
        self.assertTrue(all(safe_boundary(d.blocks[0].raw_text,s.end_char) for s in p.segments))
    def test_zwj_emoji_not_cut(self):
        d=document('One 👨\u200d👩\u200d👧\u200d👦 family. Another family.')
        p=segment_narration(d,SegmentationPolicy(18,90))
        self.assertTrue(any('👨\u200d👩\u200d👧\u200d👦' in s.raw_text for s in p.segments))
    def test_decimal_not_cut(self):
        p=segment_narration(document('Value 3.14159 stays together. End.'),SegmentationPolicy(20,200))
        self.assertTrue(any('3.14159' in s.raw_text for s in p.segments))
    def test_abbreviation_not_sentence(self):
        d=document('Dr. Rao speaks. Final words.')
        p=segment_narration(d,SegmentationPolicy(20,200))
        self.assertEqual(p.segments[0].raw_text,'Dr. Rao speaks. ')
    def test_never_merges_scenes_or_voices(self):
        d=replace(document(),blocks=(block('A.',block_id='a'),block('B.',block_id='b',scene_id='scene2',voice_id='other')))
        p=segment_narration(d);self.assertEqual([s.voice_id for s in p.segments],['voice1','other'])
    def test_input_order_not_sorted_by_id(self):
        d=replace(document(),blocks=(block('First.',block_id='z'),block('Second.',block_id='a')))
        self.assertEqual([s.block_id for s in segment_narration(d).segments],['z','a'])
    def test_noncontiguous_scenes_rejected(self):
        d=replace(document(),blocks=(block(block_id='a'),block(block_id='b',scene_id='other'),block(block_id='c')))
        self.assertRaisesRegex(AudioError,'NONCONTIGUOUS',segment_narration,d)
    def test_stale_annotated_text_rejected(self):
        d=document('abc',annotations=(Annotation(0,2,'xy','term',source_refs=('s',)),))
        self.assertRaisesRegex(AudioError,'SOURCE_MISMATCH',segment_narration,d)
    def test_overlap_annotations_rejected(self):
        d=document('abcd',annotations=(Annotation(0,3,'abc','term',source_refs=('s',)),Annotation(2,4,'cd','term',source_refs=('s',))))
        self.assertRaisesRegex(AudioError,'OVERLAPPING',segment_narration,d)
    def test_literal_price_annotation(self):
        raw='The price is $5.';d=document(raw,annotations=(annotation(raw,'$5','verbatim'),))
        self.assertEqual(segment_narration(d).segments[0].raw_text,raw)
    def test_unclosed_math(self):
        self.assertRaisesRegex(AudioError,'UNMATCHED',segment_narration,document('Read $x+1'))
    def test_empty_math(self):
        self.assertRaisesRegex(AudioError,'EMPTY_MATH',delimited_math,'$ $')
    def test_parenthesis_math_delimiters(self):
        self.assertEqual(delimited_math(r'Read \(x+y\).')[0],(5,12,'x+y'))
    def test_surrogate_rejected(self):
        self.assertRaisesRegex(AudioError,'CODEPOINT',segment_narration,document('a\ud800b'))
    def test_control_character_rejected(self):
        self.assertRaisesRegex(AudioError,'CODEPOINT',segment_narration,document('a\x00b'))
    def test_policy_bool_rejected(self):
        self.assertRaisesRegex(AudioError,'INTEGER',segment_narration,document(),SegmentationPolicy(True,120))
    def test_unknown_policy_rejected(self):
        self.assertRaisesRegex(AudioError,'UNKNOWN_SEGMENTATION_POLICY',segment_narration,document(),SegmentationPolicy(version='other'))
    def test_duplicate_block(self):
        self.assertRaisesRegex(AudioError,'DUPLICATE_BLOCK',segment_narration,replace(document(),blocks=(block(),block())))
    def test_evidence_required(self):
        self.assertRaisesRegex(AudioError,'IDENTIFIERS',segment_narration,document(evidence_ids=()))
    def test_immutable_source(self):
        d=document()
        with self.assertRaises(FrozenInstanceError): d.revision=2
    def test_fingerprint_changes_on_voice_revision(self):
        self.assertNotEqual(document().identity,document(voice_id='v2').identity)
    def test_json_roundtrip_exact(self):
        d=document('A\r\nअ।');self.assertEqual(document_from_dict(json.loads(canonical(d))),d)
    def test_unknown_json_key(self):
        d=json.loads(canonical(document()));d['accepted']=True
        self.assertRaisesRegex(AudioError,'DOCUMENT_KEYS',document_from_dict,d)
    def test_tampered_segment_source(self):
        d=document();p=segment_narration(d)
        p=replace(p,segments=(replace(p.segments[0],raw_text='wrong'),))
        self.assertRaisesRegex(AudioError,'SEGMENT_COVERAGE',verify_segments,p,d)
    def test_tampered_acceptance(self):
        d=document();self.assertRaisesRegex(AudioError,'BINDING',verify_segments,replace(segment_narration(d),accepted=True),d)
    def test_exact_director_adoption(self):
        from bie.director.script_plan import ScriptSegment,build_script_plan
        from bie.director.voiceover_generation import generate_voiceover
        from bie.director.speech_timing import utterances_from_script
        s=build_script_plan('lesson',[ScriptSegment('z','s','explain','intent only',('source:p1',),('o',))],'voice')
        draft=generate_voiceover('z',['Actual spoken words.'],{'Actual spoken words.':['source:p1']})
        u=utterances_from_script(s,[draft],['z'])
        d=from_director(u,document_id='doc',lesson_id='lesson',expected_script_fingerprint=s.fingerprint(),domains={'z':'physics'})
        self.assertEqual(d.blocks[0].raw_text,'Actual spoken words.')
        self.assertNotIn('intent',d.blocks[0].raw_text)
        self.assertEqual(d.blocks[0].upstream_fingerprint,u[0].fingerprint())
    def test_wrong_director_revision(self):
        from bie.director.speech_timing import SpeechUtterance
        u=SpeechUtterance('u','s','sc','v','Text.','en',('e',),('o',),fingerprint('one'))
        self.assertRaisesRegex(AudioError,'STALE_SCRIPT',from_director,(u,),document_id='d',lesson_id='l',expected_script_fingerprint=fingerprint('two'),domains={'u':'physics'})
    def test_no_dict_as_director_object(self):
        self.assertRaisesRegex(AudioError,'DIRECTOR_CONTRACT',from_director,({},),document_id='d',lesson_id='l',expected_script_fingerprint=fingerprint('s'),domains={})
    def test_upstream_review_retained(self):
        from bie.director.speech_timing import SpeechUtterance
        u=SpeechUtterance('u','s','sc','v','Text.','en',('e',),('o',),fingerprint('s'),('UPSTREAM_REVIEW',))
        d=from_director((u,),document_id='d',lesson_id='l',expected_script_fingerprint=u.script_fingerprint,domains={'u':'physics'})
        self.assertEqual(segment_narration(d).segments[0].review_reasons,('UPSTREAM_REVIEW',))

    def test_annotation_must_not_split_combining_cluster(self):
        d=document('e\u0301',annotations=(Annotation(0,1,'e','term',source_refs=('s',)),))
        self.assertRaisesRegex(AudioError,'CLUSTER_SPLIT',segment_narration,d)
    def test_annotation_must_not_split_zwj_sequence(self):
        d=document('👨\u200d👩',annotations=(Annotation(0,1,'👨','verbatim',source_refs=('s',)),))
        self.assertRaisesRegex(AudioError,'CLUSTER_SPLIT',segment_narration,d)
