import unittest,json
from dataclasses import asdict
from bie.audio.common import AudioError,fingerprint
from bie.audio.qa_accessibility import accessibility_qa,export_accessible,CaptionQAPolicy,SoundMeaning,SpeakerIdentity
from .qa_test_support import native,intent

class AccessibilityQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s,cls.m,cls.w=native(True)
    def test_meaningful_sound_captions_added(self):
        r,a=accessibility_qa(self.m,self.s,intent(self.m));self.assertTrue(any('[Brief tone marks the demonstration]' in str(c['lines']) for c in a['cues']))
    def test_speech_kept_with_overlapping_sound(self):
        r,a=accessibility_qa(self.m,self.s,intent(self.m));self.assertTrue(any(len(c['source_event_ids'])>1 for c in a['cues']))
    def test_original_display_track_not_rewritten(self):
        before=self.m.clock_json;accessibility_qa(self.m,self.s,intent(self.m));self.assertEqual(before,self.m.clock_json)
    def test_missing_meaning_review_not_guessed(self):
        r,a=accessibility_qa(self.m,self.s);self.assertIn('SOUND_MEANING_UNDECLARED',[f.code for f in r.findings]);self.assertFalse(any(e['kind']=='sound' for e in a['source_events']))
    def test_explicit_nonmeaningful_no_sfx_caption(self):
        i=intent(self.m);i['sounds'][0].update(meaningful=False,caption=None);r,a=accessibility_qa(self.m,self.s,i);self.assertFalse(any(e['kind']=='sound' for e in a['source_events']))
    def test_unknown_sound_rejected(self):
        i=intent(self.m);i['sounds'][0]['asset_id']='missing'
        with self.assertRaises(AudioError):accessibility_qa(self.m,self.s,i)
    def test_stale_intent_rejected(self):
        i=intent(self.m);i['mix_fingerprint']=fingerprint('stale')
        with self.assertRaises(AudioError):accessibility_qa(self.m,self.s,i)
    def test_wrong_sound_source_rejected(self):
        i=intent(self.m);i['sounds'][0]['source_refs']=['different']
        with self.assertRaises(AudioError):accessibility_qa(self.m,self.s,i)
    def test_duplicate_sound_rejected(self):
        i=intent(self.m);i['sounds']*=2
        with self.assertRaises(AudioError):accessibility_qa(self.m,self.s,i)
    def test_speaker_authored_label_applied(self):
        i=intent(self.m);i['speakers']=[{'persona_id':self.s.plan.segments[0].persona_id,'label':'Teacher','source_refs':['synthetic:authored-label']}]
        _,a=accessibility_qa(self.m,self.s,i);self.assertTrue(any('Teacher:' in e['text'] for e in a['source_events']))
    def test_unknown_speaker_rejected(self):
        i=intent(self.m);i['speakers']=[{'persona_id':'unknown','label':'Teacher','source_refs':['synthetic:authored']}]
        with self.assertRaises(AudioError):accessibility_qa(self.m,self.s,i)
    def test_spoken_channel_not_equation_display_substitute(self):
        _,a=accessibility_qa(self.m,self.s,intent(self.m));events=[e for e in a['source_events'] if e['kind']=='speech']
        self.assertEqual(''.join(e['exact_source_caption']['text'] for e in events),''.join(s.spoken_text for s in self.s.plan.segments))
    def test_literal_markup_escaped(self):
        _,a=accessibility_qa(self.m,self.s,intent(self.m,'<script>not executable</script>'))
        v=export_accessible(a);self.assertNotIn('<script>',v);self.assertIn('&lt;script&gt;',v)
    def test_vtt_srt_formats(self):
        _,a=accessibility_qa(self.m,self.s,intent(self.m));v=export_accessible(a);s=export_accessible(a,'srt')
        self.assertTrue(v.startswith('WEBVTT'));self.assertEqual(v.count('-->'),len(a['cues']));self.assertIn(',',s)
    def test_unsupported_format_rejected(self):
        _,a=accessibility_qa(self.m,self.s,intent(self.m))
        with self.assertRaises(AudioError):export_accessible(a,'ass')
    def test_changed_caption_fingerprint_rejected(self):
        _,a=accessibility_qa(self.m,self.s,intent(self.m));a['cues'][0]['lines'][0]='changed'
        with self.assertRaises(AudioError):export_accessible(a)
    def test_readability_no_content_deletion(self):
        r,a=accessibility_qa(self.m,self.s,intent(self.m,'A'*150),CaptionQAPolicy(max_chars_per_line=8))
        self.assertIn('CAPTION_REFLOW_REQUIRED',[f.code for f in r.findings]);self.assertIn('A'*150,export_accessible(a))
    def test_excessive_reading_rate_review(self):
        r,a=accessibility_qa(self.m,self.s,intent(self.m),CaptionQAPolicy(max_chars_per_second=1));self.assertIn('CAPTION_READING_TIME_REQUIRED',[f.code for f in r.findings])
    def test_bool_sound_meaning_rejected(self):
        with self.assertRaises(AudioError):SoundMeaning('a',1,'noise','en',('source',))
    def test_nonmeaningful_text_conflict_rejected(self):
        with self.assertRaises(AudioError):SoundMeaning('a',False,'noise','en',('source',))
    def test_multiline_speaker_rejected(self):
        with self.assertRaises(AudioError):SpeakerIdentity('p','a\nb',('source',))
    def test_no_wcag_acceptance_claim(self):
        r,a=accessibility_qa(self.m,self.s,intent(self.m));self.assertEqual(r.status,'REVIEW');self.assertFalse(a['rendered_accessibility_verified']);self.assertFalse(json.loads(r.metrics_json)['wcag_compliance_claimed'])
