from ped_helpers import *
from bie.qa.pedagogy_v2.metrics import event_windows,text_codepoints,text_identity,rate,overlaps
from fractions import Fraction
import random

class LoadTests(FixtureCase):
 def test_visual_peak_not_average(self):
  r=self.event('e1-objective',visual_units=4)
  r=replace(r,events=change(r.events,'event_id','e1-rubric',start_ms=0,end_ms=3000,visual_units=1))
  self.assertCode(self.run_check(r),'cognitive_load','VISUAL_PEAK_LOAD_LIMIT')
 def test_motion_peak(self):self.assertCode(self.run_check(self.event('e1-example',motion_units=4)),'cognitive_load','MOTION_PEAK_LOAD_LIMIT')
 def test_new_concept_peak(self):
  self.assertCode(self.run_check(self.event('e1-example',new_concept_ids=('concept-1','concept-2')),self.limit(max_simultaneous_new_concepts=1)),'cognitive_load','NEW_CONCEPT_PEAK_LOAD_LIMIT')
 def test_fast_text_fails(self):self.assertCode(self.run_check(self.event('e1-example',end_ms=12001)),'cognitive_load','TEXT_PRESENTATION_RATE_LIMIT')
 def test_policy_text_rate_not_global_constant(self):
  self.assertCode(self.run_check(p=self.limit(max_text_codepoints_per_minute=10)),'cognitive_load','TEXT_PRESENTATION_RATE_LIMIT')
 def test_adjacent_concept_limit(self):
  self.assertCode(self.run_check(self.event('e1-prompt',new_concept_ids=('concept-2',)),self.limit(max_adjacent_new_concepts=1)),'cognitive_load','ADJACENT_CONCEPT_LOAD_LIMIT')
 def test_uninterrupted_limit(self):self.assertCode(self.run_check(p=self.limit(max_uninterrupted_ms=99999)),'cognitive_load','UNINTERRUPTED_LOAD_LIMIT')
 def test_exact_uninterrupted_limit(self):self.assertEqual(self.run_check(p=self.limit(max_uninterrupted_ms=100000)).cognitive_load.status,'CHECKS_PASSED')
 def rest(self,duration):
  sid='real-break';ids=('instruction-1','assessment-1',sid,'instruction-2','assessment-2')
  r=replace(self.request,segments=self.request.segments+(Segment(sid,'break',duration),),routes=(Route('core-route',ids),))
  p=replace(self.limit(max_uninterrupted_ms=60000),expected_segment_ids=self.policy.expected_segment_ids+(sid,),routes=(replace(self.policy.routes[0],segment_ids=ids),))
  return r,p
 def test_sufficient_break_resets_declared_run(self):
  r,p=self.rest(5000);self.assertEqual(self.run_check(r,p).cognitive_load.status,'CHECKS_PASSED')
 def test_short_break_cannot_reset(self):
  r,p=self.rest(4999);self.assertCode(self.run_check(r,p),'cognitive_load','UNINTERRUPTED_LOAD_LIMIT')
 def test_content_cannot_hide_in_break(self):
  r=replace(self.request,segments=change(self.request.segments,'segment_id','instruction-1',kind='break'))
  self.assertCode(self.run_check(r),'cognitive_load','BREAK_CONTAINS_CONTENT')
 def test_numeric_load_is_not_mastery_evidence(self):
  x=self.run_check();self.assertFalse(x.product_accepted);self.assertTrue(any('not scientifically' in s for s in x.cognitive_load.limitations))
 def test_half_open_windows_do_not_overlap_at_boundary(self):
  a=Event('a','s',0,10,'action',(),(),3,2);b=Event('b','s',10,20,'action',(),(),4,1)
  self.assertEqual(tuple(event_windows((a,b))),((0,10,3,2,0,('a',)),(10,20,4,1,0,('b',))))
 def test_sweep_line_matches_bruteforce(self):
  rng=random.Random(16006)
  for sample in range(60):
   events=tuple(Event(f'e{i}','s',start:=rng.randrange(0,12),start+rng.randrange(1,6),'action',(),('c'+str(i%3),),rng.randrange(4),rng.randrange(3)) for i in range(10))
   windows=tuple(event_windows(events))
   for t in range(17):
    with self.subTest(sample=sample,time=t):
     active=[e for e in events if e.start_ms<=t<e.end_ms];matched=[w for w in windows if w[0]<=t<w[1]]
     if not active:self.assertFalse(matched)
     else:self.assertEqual((sum(e.visual_units for e in active),sum(e.motion_units for e in active),len({c for e in active for c in e.new_concept_ids}),tuple(sorted(e.event_id for e in active))),matched[0][2:])
 def test_overlap_text_not_counted_twice(self):
  c=self.request.source.claims[0];d=replace(c,claim_id='alias');self.assertEqual(text_codepoints({'a':c,'b':d},('a','b')),sum(not x.isspace() for x in c.text))
 def test_partial_overlap_union(self):
  c=self.request.source.claims[0];d=replace(c,claim_id='suffix',start=c.start+5,text=c.text[5:]);self.assertEqual(text_codepoints({'a':c,'b':d},('b','a')),text_codepoints({'a':c},('a',)))
 def test_separate_output_spans_not_merged(self):
  c=self.request.source.claims[0];d=replace(c,claim_id='separate',output_id='other');self.assertEqual(text_codepoints({'a':c,'b':d},('a','b')),2*text_codepoints({'a':c},('a',)))
 def test_unicode_codepoints_not_claimed_words(self):
  c=self.request.source.claims[0];text='क ख ग';d=replace(c,text=text,start=0,end=len(text));self.assertEqual(text_codepoints({'d':d},('d',)),3)
 def test_fingerprint_normalizes_whitespace_case(self):
  c=self.request.source.claims[0];d=replace(c,text=c.text.upper().replace(' ','   '),end=c.start+len(c.text.upper().replace(' ','   ')))
  self.assertEqual(text_identity({'a':c},('a',)),text_identity({'a':d},('a',)))
 def test_rate_exact_fraction(self):self.assertEqual(rate(1,7),Fraction(60000,7))
 def test_union_count_property(self):
  base=self.request.source.claims[0];text=base.text
  for start in range(len(text)):
   a=replace(base,claim_id='a',end=base.start+start+1,text=text[:start+1]);b=replace(base,claim_id='b',start=base.start+start,text=text[start:])
   with self.subTest(split=start):self.assertEqual(text_codepoints({'a':a,'b':b},('b','a')),sum(not x.isspace() for x in text))
