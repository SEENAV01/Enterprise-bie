import unittest, random
from dataclasses import replace
from fractions import Fraction
from bie.qa.director_v2.metrics import *
from bie.qa.director_v2.models import Beat
from bie.qa.source_v2.models import Claim

class Metrics(unittest.TestCase):
    def test_exact_rate(self):self.assertEqual(rate(25,1500),Fraction(1000))
    def test_ceiling(self):self.assertEqual(ceil_fraction(Fraction(10,3)),4)
    def test_whitespace_not_counted(self):self.assertEqual(codepoints(' a\n b\t'),2)
    def test_unicode_not_utf8_byte_count(self):self.assertEqual(codepoints('你好 世界'),4)
    def test_english_term_boundary(self):self.assertFalse(contains_term('megagroups','groups'));self.assertTrue(contains_term('Equal groups.','equal groups'))
    def test_term_regex_not_executed(self):self.assertTrue(contains_term('Use x.*y now','x.*y'));self.assertFalse(contains_term('Use xAAy now','x.*y'))
    def test_term_nfc(self):self.assertTrue(contains_term('cafe\u0301','café'))
    def test_hindi_term_boundary(self):self.assertTrue(contains_term('यह गति है','गति'));self.assertFalse(contains_term('गतिमान','गति'))
    def test_linguistic_joiners_not_blanket_banned(self):self.assertFalse(has_unsafe_controls('क्\u200dष'))
    def test_bidi_override_is_detected(self):self.assertTrue(has_unsafe_controls('x\u202ey'))
    def test_replacement_character_detected(self):self.assertTrue(has_unsafe_controls('x\ufffd'))
    def test_sentence_guardrail_handles_devanagari(self):self.assertEqual(sentence_lengths('अब पढ़ें। फिर करें।'),[7,7])
    def test_identity_normalizes_whitespace(self):self.assertEqual(identity(' Equal\n Groups '),'equal groups')
    def test_needs_expanded_math(self):self.assertTrue(needs_expanded_readout('x = y'));self.assertFalse(needs_expanded_readout('two groups'))
    def test_adjacent_beats_half_open(self):
        a=Beat('a','s','hook','narration',0,10,('a',),());b=Beat('b','s','recap','narration',10,20,('b',),())
        self.assertEqual(list(windows((a,b))),[(0,10,('a',)),(10,20,('b',))])
    def test_random_interval_sweep_against_independent_integer_grid(self):
        rng=random.Random(20260927)
        for trial in range(200):
            events=[]
            for i in range(rng.randint(1,12)):
                a=rng.randint(0,30);b=rng.randint(a+1,40)
                events.append(Beat('b'+str(i),'s','hook','narration',a,b,('c',),()))
            observed={t:ids for a,b,ids in windows(events) for t in range(a,b)}
            expected={t:tuple(sorted(e.beat_id for e in events if e.start_ms<=t<e.end_ms)) for t in range(min(e.start_ms for e in events),max(e.end_ms for e in events))}
            with self.subTest(trial=trial):self.assertEqual(observed,expected)
    def test_rates_against_fraction_oracle(self):
        for n in range(0,30):
            for d in (1,7,1000,4001):
                with self.subTest(n=n,d=d):self.assertEqual(rate(n,d),Fraction(n*60000,d))
    def test_overlapping_claims_not_double_counted(self):
        a=Claim('a','out','0'*64,0,5,'abcde','FACT',())
        b=Claim('b','out','0'*64,3,8,'defgh','FACT',())
        self.assertEqual(merged_text({'a':a,'b':b},('a','b')),'abcdefgh')
    def test_nested_spans_not_double_counted(self):
        a=Claim('a','out','0'*64,0,5,'abcde','FACT',());b=Claim('b','out','0'*64,1,3,'bc','FACT',())
        self.assertEqual(merged_text({'a':a,'b':b},('a','b')),'abcde')
    def test_adjacent_claims_no_inserted_word_gap(self):
        a=Claim('a','out','0'*64,0,3,'abc','FACT',());b=Claim('b','out','0'*64,3,5,'de','FACT',())
        self.assertEqual(merged_text({'a':a,'b':b},('a','b')),'abcde')
    def test_conflicting_overlap_rejected(self):
        a=Claim('a','out','0'*64,0,5,'abcde','FACT',());b=Claim('b','out','0'*64,3,6,'XYZ','FACT',())
        with self.assertRaises(ContractError):merged_text({'a':a,'b':b},('a','b'))
    def test_gap_does_not_join_words(self):
        a=Claim('a','out','0'*64,0,3,'abc','FACT',());b=Claim('b','out','0'*64,4,6,'de','FACT',())
        self.assertEqual(merged_text({'a':a,'b':b},('a','b')),'abc\nde')
