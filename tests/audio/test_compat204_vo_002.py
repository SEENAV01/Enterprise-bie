from dataclasses import replace,FrozenInstanceError
import json,unittest
from bie.audio.compat204.contracts import AudioError,canonical
from bie.audio.compat204.pronunciation_lexicon import *
from tests.audio.compat204_support import rule

class LexiconTests(unittest.TestCase):
    def lex(self,*rules):return Lexicon('l','1',tuple(rules))
    def test_literal_match(self):
        l=self.lex(rule('Coulomb','term','alias','koo lom'))
        self.assertEqual(match_lexicon('Coulomb law',l,language='en',domain='physics')[0].rule.spoken,'koo lom')
    def test_no_substring_word_match(self):
        self.assertFalse(match_lexicon('leadership',self.lex(rule('lead','term','alias','led')),language='en',domain='metal'))
    def test_combining_mark_boundary(self):
        self.assertFalse(match_lexicon('e\u0301',self.lex(rule('e','term','alias','ee')),language='en',domain='d'))
    def test_longest_phrase(self):
        l=self.lex(rule('New','term','alias','new'),rule('New Delhi','term','alias','new delhi'))
        self.assertEqual(match_lexicon('New Delhi',l,language='en',domain='d')[0].rule.surface,'New Delhi')
    def test_domain_specific_over_global(self):
        l=self.lex(rule('lead','term','alias','leed',rule_id='a'),rule('lead','term','alias','led',rule_id='b',domain='chemistry'))
        self.assertEqual(l.resolve('lead',kind='term',language='en',domain='chemistry').spoken,'led')
    def test_other_domain_no_implicit_match(self):
        l=self.lex(rule('lead','term','alias','led',domain='chemistry'))
        self.assertIsNone(l.resolve('lead',kind='term',language='en',domain='leadership'))
    def test_exact_locale_only(self):
        l=self.lex(rule('lead','term','alias','led',language='en-US'))
        self.assertIsNone(l.resolve('lead',kind='term',language='en-GB',domain='d'))
    def test_case_is_not_collapsed(self):
        l=self.lex(rule('US','acronym','letters'))
        self.assertFalse(match_lexicon('us',l,language='en',domain='d'))
    def test_duplicate_id_rejected(self):
        self.assertRaisesRegex(AudioError,'DUPLICATE_RULE_ID',self.lex(rule('A'),rule('B',rule_id='rule:A')).validate)
    def test_duplicate_selector_rejected(self):
        self.assertRaisesRegex(AudioError,'AMBIGUOUS_LEXICON',self.lex(rule(),rule(rule_id='other')).validate)
    def test_role_ambiguity(self):
        l=self.lex(rule('μ','symbol','alias','mu',role='name',rule_id='a'),rule('μ','symbol','alias','micro',role='prefix',rule_id='b'))
        self.assertRaisesRegex(AudioError,'AMBIGUOUS',l.resolve,'μ',kind='symbol',language='en',domain='physics')
    def test_cross_kind_ambiguity(self):
        l=self.lex(rule('US'),rule('US','term','alias','us',rule_id='other'))
        self.assertRaisesRegex(AudioError,'AMBIGUOUS',match_lexicon,'US',l,language='en',domain='d')
    def test_explicit_rule_must_match_source(self):
        self.assertRaisesRegex(AudioError,'EXPLICIT_RULE',self.lex(rule()).resolve,'RNA',kind='acronym',language='en',domain='d',rule_id='rule:DNA')
    def test_explicit_rule_must_match_domain(self):
        l=self.lex(rule(domain='biology'))
        self.assertRaisesRegex(AudioError,'EXPLICIT_RULE',l.resolve,'DNA',kind='acronym',language='en',domain='physics',rule_id='rule:DNA')
    def test_excluded_math_not_changed(self):
        l=self.lex(rule('x','term','alias','ex'))
        self.assertFalse(match_lexicon('$x$',l,language='en',domain='d',excluded=((0,3),)))
    def test_two_occurrences_offsets(self):
        rows=match_lexicon('DNA and DNA',self.lex(rule()),language='en',domain='biology')
        self.assertEqual([(r.start,r.end) for r in rows],[(0,3),(8,11)])
    def test_order_invariant_fingerprint(self):
        a,b=rule('DNA'),rule('RNA')
        self.assertEqual(self.lex(a,b).identity,self.lex(b,a).identity)
    def test_revision_changes_identity(self):
        a=rule();self.assertNotEqual(self.lex(a).identity,self.lex(replace(a,revision='2')).identity)
    def test_source_refs_change_identity(self):
        a=rule();self.assertNotEqual(a.identity,replace(a,source_refs=('other',)).identity)
    def test_stale_identity(self):
        self.assertRaisesRegex(AudioError,'STALE_LEXICON',self.lex(rule()).resolve,'DNA',kind='acronym',language='en',domain='d',expected_identity='sha256:'+'0'*64)
    def test_empty_lexicon_allowed(self):
        self.lex().validate()
    def test_blank_alias_for_term_rejected(self):
        self.assertRaisesRegex(AudioError,'INVALID_TEXT',rule('X','term','alias','').validate)
    def test_symbol_needs_role(self):
        self.assertRaisesRegex(AudioError,'SYMBOL_ROLE',rule('μ','symbol','alias','mu').validate)
    def test_ipa_requires_alphabet(self):
        self.assertRaisesRegex(AudioError,'PHONEME_ALPHABET',rule('read','term','alias','red',phoneme='rɛd').validate)
    def test_ipa_preserved_not_verified(self):
        r=rule('read','term','alias','red',phoneme='rɛd',alphabet='ipa');r.validate();self.assertEqual(r.phoneme,'rɛd')
    def test_no_unknown_phoneme_alphabet(self):
        self.assertRaisesRegex(AudioError,'PHONEME_ALPHABET',rule('a','term','alias','a',phoneme='x',alphabet='arbitrary').validate)
    def test_list_rules_rejected(self):
        self.assertRaisesRegex(AudioError,'LEXICON_LIMIT',Lexicon('l','1',[rule()]).validate)
    def test_serialization_roundtrip(self):
        l=self.lex(rule());self.assertEqual(lexicon_from_dict(json.loads(canonical(l))),l)
    def test_unknown_serialized_fields(self):
        raw=json.loads(canonical(self.lex(rule())));raw['rules'][0]['verified']=True
        self.assertRaisesRegex(AudioError,'RULE_KEYS',lexicon_from_dict,raw)
    def test_immutable_rules(self):
        r=rule()
        with self.assertRaises(FrozenInstanceError):r.spoken='changed'
