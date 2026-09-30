from batch002_helpers import Batch002Base, attach_fixture_tests, q, date
from copy import deepcopy
from fractions import Fraction

@attach_fixture_tests
class HIST001Tests(Batch002Base):
    task="BIE-EVAL-HIST-001"

    def test_all_required_events_missing_remain_failures(self):
        d={'op':'audit_timeline','required_event_ids':['estates_general_opening','tennis_court_oath'],'entries':[]};v=self.values(d);self.assertFalse(v['consistent']);self.assertEqual(2,len(v['defects']))
    def test_duplicate_timeline_events_not_counted_twice(self):
        d=self.input(4);d['entries']*=2;self.rejected(d,'DUPLICATE_EVENT')
    def test_unexpected_event_refused(self):
        d=self.input(4);d['required_event_ids']=['estates_general_opening'];self.rejected(d,'UNEXPECTED_EVENT')
    def test_claim_source_mismatch_is_rejection(self):
        d=self.input(9);d['source_ref']='wrong-reference';self.rejected(d,'CLAIM_SOURCE_MISMATCH')
    def test_textual_principle_not_historical_practice_proof(self):
        d={'op':'classify_claim','claim_id':'declaration_article16_separation_powers','source_ref':'elysee-declaration-1789'};v=self.values(d);self.assertEqual('TEXTUAL_PRINCIPLE',v['claim_type']);self.assertFalse(v['historical_practice_established_by_normative_text'])
    def test_normative_principle_not_actor_score(self):
        v=self.values(self.input(9));self.assertNotIn('actor_score',v);self.assertNotIn('winner',v)
    def test_reference_event_return_defensive_copy(self):
        d=self.input();v=self.values(d);v['events'][0]['date']='1900-01-01';self.assertEqual('1789-05-05',self.values(d)['events'][0]['date'])
    def test_candidate_cannot_override_reference_date(self):
        d=self.input();d['reference_date']='1800-01-01';self.rejected(d,'INVALID_FIELDS')
    def test_julian_calendar_not_silently_converted(self):
        d=self.input(4);d['entries'][0]['date']['calendar']='julian';self.rejected(d,'UNSUPPORTED_ENUM')
    def test_declaration_date_has_no_unsourced_place_field(self):
        v=self.values({'op':'event_facts','event_ids':['declaration_1789_text']});self.assertNotIn('place',v['events'][0])
