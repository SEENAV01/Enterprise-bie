from dataclasses import replace
import hashlib,json,unittest
from pathlib import Path
from bie.audio.common import AudioError
from bie.audio.preparation_bridge import from_v144,from_v204
from bie.audio.voice_selection import select_voices,SelectionPolicy,requests_for
from bie.audio.compat204.pronunciation_lexicon import Lexicon
from tests.audio.audio_test_support import utterance,empty_options
from tests.audio.compat204_support import document
from tests.audio.tts_test_support import TestProvider

class Reconciliation(unittest.TestCase):
    def test_v144_original_text_lossless(self):
        u=utterance(' First clause.\nSecond clause! ');p=from_v144((u,),**empty_options())
        self.assertEqual(''.join(s.display_text for s in p.segments),u.text)
    def test_v204_original_text_lossless(self):
        d=document(' First clause.\nSecond clause! ');p=from_v204(d,Lexicon('empty','1',()))
        self.assertEqual(''.join(s.display_text for s in p.segments),d.blocks[0].raw_text)
    def test_different_profiles_explicit(self):
        a=from_v144((utterance('Hello world.'),),**empty_options());b=from_v204(document('Hello world.'),Lexicon('empty','1',()))
        self.assertNotEqual(a.profile,b.profile);self.assertNotEqual(a.fingerprint(),b.fingerprint())
    def test_no_automatic_math_fallback(self):
        from bie.audio.math_pronunciation import pronounce_math
        with self.assertRaises(AudioError):pronounce_math(r'\sum_{i=1}^{n}{i}','en',evidence_refs=('source:test',))
    def test_extended_sum_still_executable(self):
        from bie.audio.compat204.math_pronunciation import pronounce_math
        self.assertIn('sum',pronounce_math(r'\sum_{i=1}^{n}{i}').spoken_text)
    def test_hindi_still_executable(self):
        from bie.audio.math_pronunciation import pronounce_math
        self.assertIn('बराबर',pronounce_math('x+2=3','hi',evidence_refs=('source:test',)).reading.spoken)
    def test_both_feed_same_request_contract(self):
        provider=TestProvider()
        for p in (from_v144((utterance(),),**empty_options()),from_v204(document(),Lexicon('empty','1',()))):
            choice=select_voices(p,provider.catalog(),SelectionPolicy(('fixture-provider',),('fixture',)))
            self.assertEqual(requests_for(p,provider.catalog(),choice)[0].plan_fingerprint,p.fingerprint())
    def test_compat_unknown_review_not_erased(self):
        p=from_v204(document('Unknown XYZ.'),Lexicon('empty','1',()))
        with self.assertRaises(AudioError):p.require_ready()
    def test_current_unknown_review_not_erased(self):
        p=from_v144((utterance('Unknown XYZ.'),),**empty_options())
        with self.assertRaises(AudioError):p.require_ready()
    def test_source_refs_preserved(self):
        u=utterance();p=from_v144((u,),**empty_options())
        self.assertEqual(p.segments[0].spans[0].source_refs,u.evidence_ids)
    def test_upstream_revision_preserved(self):
        u=utterance();s=from_v144((u,),**empty_options()).segments[0]
        self.assertEqual(s.script_fingerprint,u.script_fingerprint);self.assertEqual(s.utterance_fingerprint,u.fingerprint())
    def test_literal_cannot_be_rewritten(self):
        s=from_v144((utterance(),),**empty_options()).segments[0].spans[0]
        with self.assertRaisesRegex(AudioError,'LITERAL_CHANGED'):replace(s,spoken='a different lesson')
    def test_original_zip_bytes_preserved(self):
        root=Path(__file__).resolve().parents[2]/'lineage/audio_batch001'
        expected={'BIE_AUDIO_ORIGINAL_BATCH_001_VO_001_005.zip':'dc57574f8656daec035090bf4229f8394bca6456492f0044ddf66773a110b489',
         'BIE_AUDIO_ORIGINAL_BATCH_001_VO_001_005_INTEGRATED.zip':'f0a8ae7fb4cc75d28c380612d56dfa9ee16d3bdd15b3a2b85cf764cfb07acfe9'}
        for n,d in expected.items():self.assertEqual(hashlib.sha256((root/n).read_bytes()).hexdigest(),d)
    def test_no_historical_tests_removed(self):
        root=Path(__file__).resolve().parent
        self.assertEqual(len(list(root.glob('test_compat204_vo_*.py'))),5)
        self.assertEqual(len(list(root.glob('test_audio_vo_00[1-5].py'))),5)
