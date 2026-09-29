from ped_helpers import *
from bie.qa.pedagogy_v2.metrics import text_identity

class AuditRegressionTests(FixtureCase):
 def test_replayed_event_cannot_create_second_example(self):
  es={e.event_id:e for e in self.request.events};replay=replace(es['e1-example'],event_id='replayed-example')
  t=self.request.teachings[1];alias=replace(t,teaching_id='synthetic-second',event_ids=('e1-example','replayed-example'))
  r=replace(self.request,events=self.request.events+(replay,),teachings=self.request.teachings+(alias,))
  self.assertCode(self.run_check(r,self.spec(minimum_worked_examples=2)),'objectives','WORKED_EXAMPLES_INSUFFICIENT')
 def test_same_span_alias_has_same_fingerprint(self):
  c=self.request.source.claims[0];d=replace(c,claim_id='alias')
  self.assertEqual(text_identity({'a':c,'b':d},('a','b')),text_identity({'a':c},('a',)))
 def test_overlapping_split_same_fingerprint(self):
  c=self.request.source.claims[0];a=replace(c,claim_id='part-a',end=c.start+10,text=c.text[:10]);b=replace(c,claim_id='part-b',start=c.start+5,text=c.text[5:])
  self.assertEqual(text_identity({'a':a,'b':b},('a','b')),text_identity({'c':c},('c',)))
 def test_concurrent_text_rate_not_just_per_event(self):
  # Each short display alone is below 2,500 codepoints/minute; combined they are not.
  e=Event('extra-text','assessment-1',0,3000,'screen',('c2-prompt',),(),1)
  r=replace(self.request,events=self.request.events+(e,))
  x=self.run_check(r,self.limit(max_text_codepoints_per_minute=2500));self.assertCode(x,'cognitive_load','CONCURRENT_TEXT_RATE_LIMIT')
  self.assertNotIn('TEXT_PRESENTATION_RATE_LIMIT',codes(x.cognitive_load))
