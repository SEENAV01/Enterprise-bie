from dataclasses import replace
import unittest
from bie.audio.common import AudioError,fingerprint
from bie.audio.caption_alignment import *
from bie.audio.speech_contract import SpeechSpan
from bie.audio.sync_contract import source_slices
from tests.audio.sync_test_support import fixture

class Captions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.p,cls.a,cls.t=fixture();cls.c=align_captions(cls.a[0],cls.t[0],require_measured=False)
    def test_exact_text_coverage(self):self.assertEqual(''.join(c.text for c in self.c.cues),self.p.segments[0].spoken_text)
    def test_every_word_once(self):self.assertEqual(tuple(i for c in self.c.cues for i in c.word_indexes),(0,1,2))
    def test_timings_from_words(self):self.assertEqual(self.c.cues[0].start_sample,self.t[0].words[0].start_sample);self.assertEqual(self.c.cues[-1].end_sample,self.t[0].words[-1].end_sample)
    def test_measured_required_default(self):
        with self.assertRaisesRegex(AudioError,'MEASURED'):align_captions(self.a[0],self.t[0])
    def test_display_channel(self):
        c=align_captions(self.a[0],self.t[0],CaptionPolicy(channel='display'),require_measured=False)
        self.assertEqual(c.source_text,self.p.segments[0].display_text)
    def test_wrap_does_not_truncate(self):
        c=align_captions(self.a[0],self.t[0],CaptionPolicy(max_chars_per_line=8,max_lines=1),require_measured=False)
        self.assertEqual(len(c.cues),3);self.assertEqual(''.join(x.text for x in c.cues),self.c.source_text)
    def test_long_indivisible_token_rejected(self):
        p,a,t=fixture(('Supercalifragilisticexpialidocious.',))
        with self.assertRaisesRegex(AudioError,'RESEGMENT'):align_captions(a[0],t[0],CaptionPolicy(max_chars_per_line=8),require_measured=False)
    def test_reading_speed_not_forcefit(self):
        with self.assertRaisesRegex(AudioError,'EXTENSION'):align_captions(self.a[0],self.t[0],CaptionPolicy(max_chars_per_second=1),require_measured=False)
    def test_minimum_duration_gate(self):
        with self.assertRaisesRegex(AudioError,'EXTENSION'):align_captions(self.a[0],self.t[0],CaptionPolicy(min_duration_ms=4000),require_measured=False)
    def test_duration_can_split(self):
        c=align_captions(self.a[0],self.t[0],CaptionPolicy(max_duration_ms=1000),require_measured=False);self.assertEqual(len(c.cues),3)
    def test_cue_edit_rejected(self):
        with self.assertRaisesRegex(AudioError,'TEXT_COVERAGE'):replace(self.c,cues=(replace(self.c.cues[0],text='Omega beta gamma.'),))
    def test_timing_outside_provider_rejected(self):
        with self.assertRaisesRegex(AudioError,'TIME_RANGE'):replace(self.c,cues=(replace(self.c.cues[0],end_sample=1000000),))
    def test_missing_final_character_rejected(self):
        with self.assertRaises(AudioError):replace(self.c,source_text=self.c.source_text+'X')
    def test_wrong_layout_rejected(self):
        with self.assertRaisesRegex(AudioError,'LAYOUT'):replace(self.c,cues=(replace(self.c.cues[0],lines=('fake',)),))
    def test_word_ordinal_coverage_rejected(self):
        with self.assertRaisesRegex(AudioError,'WORD_COVERAGE'):replace(self.c,cues=(replace(self.c.cues[0],word_indexes=(0,2)),))
    def test_vtt_header(self):self.assertTrue(export_captions((self.c,),(0,)).startswith('WEBVTT\n'))
    def test_srt_timestamp(self):self.assertIn(',',export_captions((self.c,),(0,),format='srt').splitlines()[1])
    def test_vtt_offset(self):self.assertIn('00:00:01.005',export_captions((self.c,),(22050,)))
    def test_export_out_of_order_rejected(self):
        with self.assertRaisesRegex(AudioError,'COLLISION'):export_captions((self.c,self.c),(0,0))
    def test_literal_markup_escaped(self):
        src='<b>Alpha</b>'
        c=CaptionTrack('s',fingerprint('a'),src,22050,44100,CaptionPolicy(),(CaptionCue('c',0,len(src),src,(src,),0,22050,(0,)),))
        self.assertIn('&lt;b&gt;Alpha&lt;/b&gt;',export_captions((c,),(0,)))
    def test_hindi_codepoints_not_split(self):
        p,a,t=fixture(('बल दिशा में लगता है।',),language='hi');c=align_captions(a[0],t[0],CaptionPolicy(channel='display'),require_measured=False)
        self.assertEqual(''.join(x.text for x in c.cues),'बल दिशा में लगता है।')
    def test_unknown_channel_rejected(self):
        with self.assertRaises(AudioError):CaptionPolicy(channel='translated')
    def test_no_empty_export(self):
        with self.assertRaises(AudioError):export_captions((),())
    def test_invalid_format(self):
        with self.assertRaises(AudioError):export_captions((self.c,),(0,),format='html')

    def test_export_mixed_sample_clocks_rejected(self):
        other=replace(self.c,sample_rate=44100)
        with self.assertRaisesRegex(AudioError,'SHARED_CLOCK'):export_captions((self.c,other),(0,200000))
