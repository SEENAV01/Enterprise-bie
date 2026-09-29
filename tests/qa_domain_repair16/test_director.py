from domain_helpers import *
class DirectorTests(Base):
 def test_overflow_duration_restored(self):
  c=self.context(7);a,w=director.repair(c.bad,c.root,c.dp);self.assertEqual(a,c.good);self.assertEqual(w['added_duration_ms'],1000)
 def test_content_and_condition_unchanged(self):
  c=self.context(7);a,w=director.repair(c.bad,c.root,c.dp)
  for f in ('source','fidelity','promises','transitions','routes','term_introductions','spoken_forms'):self.assertEqual(getattr(a,f),getattr(c.good,f))
 def test_rate_expands_duration(self):
  c=self.context(7);p=replace(c.dp,pacing=replace(c.dp.pacing,speech_codepoints_per_minute=800),routes=(replace(c.dp.routes[0],max_duration_ms=200000),));a,w=director.repair(c.bad,c.root,p);self.assertGreater(a.beats[0].end_ms-a.beats[0].start_ms,c.good.beats[0].end_ms-c.good.beats[0].start_ms)
 def test_pause_not_shortened(self):
  c=self.context(7);p=replace(c.dp,pacing=replace(c.dp.pacing,speech_codepoints_per_minute=800),routes=(replace(c.dp.routes[0],max_duration_ms=200000),));a,w=director.repair(c.bad,c.root,p);before=next(b for b in c.bad.beats if b.channel=='pause');after=next(b for b in a.beats if b.channel=='pause');self.assertEqual(after.end_ms-after.start_ms,before.end_ms-before.start_ms)
 def test_overlap_requires_redesign(self):
  c=self.context(7);r=replace(c.bad,beats=(c.bad.beats[0],replace(c.bad.beats[1],start_ms=4000))+c.bad.beats[2:]);self.assertError('DOMAIN_REPAIR_OVERLAP_REDESIGN_REQUIRED',director.repair,r,c.root,c.dp)
 def test_simultaneous_speakers_ambiguous(self):
  c=self.context(7);r=replace(c.bad,beats=(c.bad.beats[0],replace(c.bad.beats[1],start_ms=0))+c.bad.beats[2:]);self.assertError('DOMAIN_REPAIR_AMBIGUOUS_SPEAKERS',director.repair,r,c.root,c.dp)
 def test_unbound_spoken_form(self):
  c=self.context(7);f=dh.SpokenForm('b-hook','short',());r=replace(c.bad,spoken_forms=(f,));self.assertError('DOMAIN_REPAIR_SPOKEN_FORM_UNGROUNDED',director.repair,r,c.root,c.dp)
 def test_false_short_spoken_form(self):
  c=self.context(7);f=dh.SpokenForm('b-hook','short',('c-hook',));r=replace(c.bad,spoken_forms=(f,));self.assertError('DOMAIN_REPAIR_SPOKEN_FORM_MISMATCH',director.repair,r,c.root,c.dp)
 def test_route_duration_limit(self):
  c=self.context(7);p=replace(c.dp,routes=(replace(c.dp.routes[0],max_duration_ms=1),));self.assertError('DOMAIN_REPAIR_ROUTE_DURATION',director.repair,c.bad,c.root,p)
 def test_added_duration_limit(self):
  c=self.context(7);self.assertError('DOMAIN_REPAIR_TIME_BUDGET',director.repair,c.bad,c.root,c.dp,Limits(max_added_ms=0))
 def test_timing_constraint_not_dropped(self):
  c=self.context(7);p=replace(c.dp,timing_constraints=(replace(c.dp.timing_constraints[0],minimum_gap_ms=4000,maximum_gap_ms=5000),));self.assertError('DOMAIN_REPAIR_TIMING_CONSTRAINT',director.repair,c.bad,c.root,p)
 def test_unknown_scene(self):
  c=self.context(7);r=replace(c.bad,beats=c.bad.beats+(replace(c.bad.beats[0],beat_id='unknown-beat',scene_id='absent'),));self.assertError('DOMAIN_REPAIR_UNKNOWN_SCENE',director.repair,r,c.root,c.dp)
 def test_empty_scene(self):
  c=self.context(7);r=replace(c.bad,beats=tuple(b for b in c.bad.beats if b.scene_id!='s1'));self.assertError('DOMAIN_REPAIR_EMPTY_SCENE',director.repair,r,c.root,c.dp)
 def test_noop(self):
  c=self.context(7);self.assertError('DOMAIN_REPAIR_NO_CHANGE',director.repair,c.good,c.root,c.dp)
 def test_actual_pacing_evaluator(self):
  c=self.context(7);a,w=director.repair(c.bad,c.root,c.dp);out=evaluate_candidate(c.task,a,c.root,c.dp,as_of=c.now,**options(7,a,c.dp));self.assertEqual(out.pacing.status,'CHECKS_PASSED')
 def test_all_scene_inventory(self):
  c=self.context(7);self.assertError('DOMAIN_REPAIR_SCENE_SCOPE',director.repair,replace(c.bad,scenes=c.bad.scenes[1:]),c.root,c.dp)
