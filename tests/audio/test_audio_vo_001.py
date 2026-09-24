import unittest
from dataclasses import replace,FrozenInstanceError
from bie.audio.segmentation import *
from bie.audio.common import AudioError
from tests.audio.audio_test_support import director,utterance

class NarrationSegmentationTests(unittest.TestCase):
    def test_actual_director_producer(self):
        s,d,o,us=director();again,p=from_director_script(s,d,o)
        self.assertEqual(again,us);self.assertEqual(p.segments[0].display_text,d[0].text)
    def test_intent_is_not_narration(self):
        s,d,o,us=director('A real explanation.')
        _,p=from_director_script(s,d,o);self.assertNotIn('Describe',p.segments[0].display_text)
    def test_no_character_loss(self):
        u=utterance('  First sentence.\r\nSecond sentence!  Third one?\n')
        p=split_narration((u,),policy=SegmentPolicy(max_chars=24,max_utf8_bytes=96))
        self.assertEqual(''.join(s.display_text for s in p.segments),u.text)
        self.assertEqual(p.segments[0].start_char,0);self.assertEqual(p.segments[-1].end_char,len(u.text))
    def test_utf8_budget_hindi(self):
        u=utterance('यह पहला वाक्य है। यह दूसरा वाक्य है।','hi')
        p=split_narration((u,),policy=SegmentPolicy(max_chars=40,max_utf8_bytes=48))
        self.assertTrue(all(len(s.display_text.encode())<=48 for s in p.segments));self.assertEqual(''.join(s.display_text for s in p.segments),u.text)
    def test_no_combining_or_zwj_cut(self):
        u=utterance('A e\u0301 word 👩\u200d🔬 done.')
        p=split_narration((u,),policy=SegmentPolicy(max_chars=12,max_utf8_bytes=48))
        for s in p.segments:self.assertTrue(boundary(u.text,s.end_char))
    def test_decimal_not_sentence_split(self):
        u=utterance('Value 3.14 stays. Next part.')
        p=split_narration((u,),policy=SegmentPolicy(max_chars=20,max_utf8_bytes=80))
        self.assertIn('3.14',p.segments[0].display_text)
    def test_abbreviation_heuristic(self):
        p=SegmentPolicy(max_chars=18,max_utf8_bytes=80)
        u=utterance('Dr. Rao explains force. Next.')
        self.assertNotIn(4,__import__('bie.audio.segmentation',fromlist=['_sentences'])._sentences(u.text,p))
    def test_protected_math_not_split(self):
        u=utterance('Read a + b = c clearly.')
        x=ProtectedSpan(u.utterance_id,5,14,'a + b = c',u.fingerprint(),'math')
        p=split_narration((u,),policy=SegmentPolicy(max_chars=15,max_utf8_bytes=60),protected=(x,))
        self.assertTrue(any('a + b = c' in s.display_text for s in p.segments))
    def test_indivisible_fail_not_truncate(self):
        u=utterance('a'*50)
        with self.assertRaisesRegex(AudioError,'INDIVISIBLE'):split_narration((u,),policy=SegmentPolicy(max_chars=8,max_utf8_bytes=16))
    def test_stale_protected(self):
        u=utterance('word next');p=ProtectedSpan(u.utterance_id,0,4,'word','sha256:'+'0'*64)
        with self.assertRaisesRegex(AudioError,'STALE'):split_narration((u,),protected=(p,))
    def test_wrong_protected_text(self):
        u=utterance('word next');p=ProtectedSpan(u.utterance_id,0,4,'xxxx',u.fingerprint())
        with self.assertRaisesRegex(AudioError,'TEXT_MISMATCH'):split_narration((u,),protected=(p,))
    def test_overlap_reject(self):
        u=utterance('one two three');ps=(ProtectedSpan('s1',0,7,'one two',u.fingerprint()),ProtectedSpan('s1',4,13,'two three',u.fingerprint()))
        with self.assertRaisesRegex(AudioError,'OVERLAPPING'):split_narration((u,),protected=ps)
    def test_pause_preserved(self):
        u=utterance('Wait. Then explain.');p=split_narration((u,),pauses=(Pause('s1',5,1500,('dir:pause',)),))
        self.assertEqual(p.segments[0].pause_after_ms,1500);self.assertEqual(p.segments[0].pause_refs,('dir:pause',));self.assertEqual(''.join(s.display_text for s in p.segments),u.text)
    def test_pause_inside_word_reject(self):
        with self.assertRaisesRegex(AudioError,'SPLITS_TOKEN'):split_narration((utterance('Explanation.'),),pauses=(Pause('s1',3,100,('e',)),))
    def test_pause_inside_math_reject(self):
        u=utterance('a plus b then');p=ProtectedSpan('s1',0,8,'a plus b',u.fingerprint(),'math')
        with self.assertRaisesRegex(AudioError,'SPLITS_PROTECTED'):split_narration((u,),protected=(p,),pauses=(Pause('s1',2,100,('e',)),))
    def test_duplicate_pause_reject(self):
        u=utterance('Wait.');p=Pause('s1',5,100,('e',))
        with self.assertRaisesRegex(AudioError,'DUPLICATE_PAUSE'):split_narration((u,),pauses=(p,p))
    def test_upstream_review_retained(self):
        u=replace(utterance(),review_reasons=('UPSTREAM_REVIEW',))
        self.assertEqual(split_narration((u,)).segments[0].review_reasons,u.review_reasons)
    def test_scene_and_voice_preserved(self):
        u=utterance();s=split_narration((u,)).segments[0]
        self.assertEqual((s.scene_id,s.voice_id,s.evidence_ids,s.objective_ids),(u.scene_id,u.voice_id,u.evidence_ids,u.objective_ids))
    def test_revision_mix_reject(self):
        a=utterance();b=replace(a,utterance_id='other',script_fingerprint='sha256:'+'0'*64)
        with self.assertRaisesRegex(ValueError,'revisions'):split_narration((a,b))
    def test_explicit_order_not_sorted(self):
        from bie.director.script_plan import ScriptSegment,build_script_plan
        from bie.director.voiceover_generation import generate_voiceover
        s=build_script_plan('L',tuple(ScriptSegment(i,i,'EXPLAIN','intent',('e',),('o',)) for i in ('10','2')),'voice')
        drafts=tuple(generate_voiceover(i,(i+' text',),{i+' text':('e',)}) for i in ('10','2'))
        _,p=from_director_script(s,drafts,('2','10'));self.assertEqual([x.utterance_id for x in p.segments],['2','10'])
    def test_bool_limits_reject(self):
        with self.assertRaises(AudioError):SegmentPolicy(max_chars=True)
    def test_resource_segment_limit(self):
        with self.assertRaisesRegex(AudioError,'SEGMENT_RESOURCE'):split_narration((utterance('one two three four five six seven eight'),),policy=SegmentPolicy(max_chars=8,max_utf8_bytes=32,max_segments=2))
    def test_revalidate_detects_edit(self):
        u=utterance();p=split_narration((u,));bad=replace(p,segments=(replace(p.segments[0],display_text='changed'),))
        with self.assertRaisesRegex(AudioError,'STALE_OR_EDITED'):validate_plan(bad,(u,))
    def test_stable_fingerprint_and_no_audio_claim(self):
        u=utterance();a=split_narration((u,));b=split_narration((u,));self.assertEqual(a.fingerprint(),b.fingerprint());self.assertFalse(a.accepted);self.assertFalse(a.audio_generated)
