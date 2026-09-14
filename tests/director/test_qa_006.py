from dataclasses import replace
import unittest
from qa_fixtures import codes, case
from pacing_fixtures import timed, beat, evaluate
from bie.director.pacing_qa import PacingPolicy, validate_pacing_report
from bie.director.pause_timing import PauseCue
from bie.director.speech_timing import ReportedAlignment
from bie.director.scene_duration_fit import fit_scene_durations
from bie.director.pacing_plan import ScenePacing


class PacingTests(unittest.TestCase):
    def test_estimate_retains_uncertainty_and_full_content(self):
        c=timed(); r=evaluate(c,(beat(c),))
        self.assertEqual(r.status,"REVIEW_REQUIRED")
        self.assertIn("UNCALIBRATED_WPM_ESTIMATE",codes(r))
        self.assertNotIn("PACING_ANNOTATION_INCOMPLETE",codes(r))
        self.assertEqual(dict(r.measurements)["total_duration_ms"],2400)
        self.assertFalse(r.accepted)

    def test_unannotated_material_is_not_silently_certified(self):
        self.assertIn("PACING_ANNOTATION_INCOMPLETE",codes(evaluate(timed())))

    def test_explicit_reflection_requires_silence_after_that_span(self):
        c=timed(); r=evaluate(c,(beat(c,minimum=2000),))
        self.assertEqual(r.status,"BLOCKED")
        self.assertIn("REQUIRED_REFLECTION_SHORTFALL",codes(r))

    def test_reflection_exact_boundary_values(self):
        for pause, expected in ((1999,True),(2000,False),(2001,False)):
            with self.subTest(pause=pause):
                c=timed(cues=(PauseCue("p","u1",6,pause,"Think about the concept",("e1",)),))
                self.assertEqual("REQUIRED_REFLECTION_SHORTFALL" in codes(evaluate(c,(beat(c,minimum=2000),))),expected)

    def test_pause_at_wrong_place_does_not_satisfy_reflection(self):
        c=timed(cues=(PauseCue("p","u1",0,4000,"Before narration",("e1",)),))
        self.assertIn("REQUIRED_REFLECTION_SHORTFALL",codes(evaluate(c,(beat(c,minimum=2000),))))

    def test_within_utterance_reflection(self):
        c=timed(cues=(PauseCue("p","u1",2,2000,"Reflect now",("e1",)),))
        r=evaluate(c,(beat(c,end=len("A triangle"),minimum=2000),))
        self.assertNotIn("REQUIRED_REFLECTION_SHORTFALL",codes(r))
        self.assertEqual(dict(r.measurements)["beat:b:u1:following_silence_ms"],2000)

    def test_shared_tail_head_pause_not_double_counted(self):
        c=timed(("A triangle has three sides.","A square has four sides."),cues=(PauseCue("tail","u1",5,2000,"Think",("e1",)),PauseCue("head","u2",0,2000,"Think",("e2",))))
        r=evaluate(c,(beat(c,minimum=2000),beat(c,"u2")))
        self.assertEqual(dict(r.measurements)["beat:b:u1:following_silence_ms"],2000)
        self.assertEqual(c.timeline.duration_ms,6000)

    def test_scene_cut_is_not_an_implicit_pause(self):
        c=timed(("A triangle has three sides.","A square has four sides."),scene_ids=("s1","s2"))
        self.assertIn("REQUIRED_REFLECTION_SHORTFALL",codes(evaluate(c,(beat(c,minimum=1000),beat(c,"u2")))))

    def test_reported_pause_shortfall_routes_to_audio(self):
        u=case().snapshot.utterances[0]
        a=ReportedAlignment(u.fingerprint(),"sha256:"+"a"*64,2400,tuple((i*400,(i+1)*400) for i in range(6)),"fixture")
        c=timed(alignments=(a,),cues=(PauseCue("p","u1",6,2000,"Think",("e1",)),)); r=evaluate(c,(beat(c,minimum=2000),))
        self.assertEqual(c.timeline.duration_ms,2400)
        self.assertTrue(all(f.repair_stage=="AUDIO" for f in r.findings if f.severity=="BLOCKER"))

    def test_reported_audio_remains_unverified_even_with_correct_pause(self):
        u=case().snapshot.utterances[0]
        a=ReportedAlignment(u.fingerprint(),"sha256:"+"a"*64,4400,tuple((i*400,(i+1)*400) for i in range(6)),"fixture")
        c=timed(alignments=(a,)); r=evaluate(c,(beat(c,minimum=2000),))
        self.assertNotIn("REQUIRED_REFLECTION_SHORTFALL",codes(r))
        self.assertIn("REPORTED_ALIGNMENT_REQUIRES_AUDIO_QA",codes(r))

    def test_silence_cannot_hide_excessive_active_rate(self):
        u=case().snapshot.utterances[0]
        a=ReportedAlignment(u.fingerprint(),"sha256:"+"a"*64,20000,tuple((i*100,(i+1)*100) for i in range(6)),"fixture")
        c=timed(alignments=(a,)); r=evaluate(c,(beat(c),))
        self.assertEqual(dict(r.measurements)["utterance:u1:active_wpm"],600)
        self.assertIn("SPEECH_RATE_OUTSIDE_POLICY",codes(r)); self.assertIn("UNEXPLAINED_SILENCE_REVIEW",codes(r))

    def test_rolling_window_detects_rush_hidden_by_slow_words(self):
        text=" ".join(["word"]*24); u=case((text,)).snapshot.utterances[0]
        intervals=tuple((i*100,(i+1)*100) for i in range(12))+tuple((1200+i*1000,1200+(i+1)*1000) for i in range(12))
        c=timed((text,),alignments=(ReportedAlignment(u.fingerprint(),"sha256:"+"a"*64,13200,intervals,"fixture"),)); r=evaluate(c,(beat(c),))
        self.assertNotIn("SPEECH_RATE_OUTSIDE_POLICY",codes(r)); self.assertIn("RUSHED_SPEECH_WINDOW",codes(r))

    def test_abrupt_rate_change(self):
        texts=(" ".join(["word"]*12)," ".join(["term"]*12)); c0=case(texts)
        aligns=tuple(ReportedAlignment(u.fingerprint(),"sha256:"+str(i+1)*64,12*ms,tuple((n*ms,(n+1)*ms) for n in range(12)),"fixture") for i,(u,ms) in enumerate(zip(c0.snapshot.utterances,(300,750))))
        c=timed(texts,alignments=aligns)
        self.assertIn("ABRUPT_RATE_CHANGE",codes(evaluate(c,(beat(c),beat(c,"u2")))))

    def test_reasoning_rate_and_reflection_heuristics(self):
        c=timed(wpm=200); r=evaluate(c,(beat(c,mode="DERIVE"),))
        self.assertIn("REASONING_PACE_REVIEW",codes(r)); self.assertIn("REFLECTION_OPPORTUNITY_REVIEW",codes(r))
        self.assertNotEqual(r.status,"BLOCKED")

    def test_retrieval_heuristic_is_distinct_from_explicit_contract(self):
        c=timed(); r=evaluate(c,(beat(c,mode="RETRIEVE"),))
        self.assertIn("REFLECTION_OPPORTUNITY_REVIEW",codes(r)); self.assertNotIn("REQUIRED_REFLECTION_SHORTFALL",codes(r))

    def test_long_content_is_retained_without_duration_cap(self):
        c=timed((" ".join(["concept"]*400),)); r=evaluate(c,(beat(c),))
        self.assertEqual(c.timeline.duration_ms,160000); self.assertIn("CONTINUOUS_SPEECH_REVIEW",codes(r))
        self.assertNotEqual(r.status,"BLOCKED")

    def test_short_gaps_accumulate_as_one_break(self):
        c0=case(("A triangle has three sides.","A square has four sides."))
        aligns=tuple(ReportedAlignment(u.fingerprint(),"sha256:"+str(i+1)*64,2400,tuple((200+n*400,200+(n+1)*400) for n in range(5)),"fixture") for i,u in enumerate(c0.snapshot.utterances))
        c=timed(tuple(u.text for u in c0.snapshot.utterances),alignments=aligns)
        r=evaluate(c,policy=replace(PacingPolicy(),break_ms=400,continuous_speech_review_ms=3000))
        self.assertEqual(dict(r.measurements)["longest_continuous_speech_ms"],2000)
        self.assertNotIn("CONTINUOUS_SPEECH_REVIEW",codes(r))

    def test_soft_scene_target_routes_to_replanning_not_truncation(self):
        c=timed(); c.timeline=fit_scene_durations(c.speech,c.pauses,c.emphasis,(ScenePacing("scene1",1,"NORMAL","soft target"),))
        self.assertIn("SCENE_TARGET_REQUIRES_REPLAN",codes(evaluate(c,(beat(c),)))); self.assertEqual(c.timeline.duration_ms,2400)

    def test_changed_script_or_timeline_is_rejected(self):
        c=timed(); c.snapshot=case(("A triangle has four straight sides.",)).snapshot
        with self.assertRaises(ValueError): evaluate(c)
        c=timed(); c.timeline=replace(c.timeline,scenes=(replace(c.timeline.scenes[0],duration_ms=1),))
        with self.assertRaises(ValueError): evaluate(c)

    def test_beat_revision_grounding_overlap_and_types(self):
        c=timed(); b=beat(c)
        for bad in (replace(b,evidence_ids=("unknown",)),replace(b,minimum_reflection_ms=True),replace(b,mode="QUIZ"),replace(b,span=replace(b.span,utterance_fingerprint="sha256:"+"a"*64))):
            with self.subTest(bad=bad),self.assertRaises(ValueError): evaluate(c,(bad,))
        with self.assertRaises(ValueError): evaluate(c,(b,replace(b,beat_id="duplicate")))
        with self.assertRaises(ValueError): evaluate(c,[b])

    def test_report_revision_and_policy_are_verified(self):
        c=timed(); b=(beat(c),); r=evaluate(c,b)
        self.assertEqual(validate_pacing_report(r,c.snapshot,c.speech,c.pauses,c.emphasis,c.timeline,b),r)
        for modified in (replace(r,findings=()),replace(r,inputs_fingerprint="sha256:"+"a"*64)):
            with self.assertRaises(ValueError): validate_pacing_report(modified,c.snapshot,c.speech,c.pauses,c.emphasis,c.timeline,b)
        with self.assertRaises(ValueError): evaluate(c,policy=replace(PacingPolicy(),maximum_wpm=float("nan")))


if __name__=="__main__": unittest.main()
