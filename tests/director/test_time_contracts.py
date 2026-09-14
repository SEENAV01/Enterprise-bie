"""Cross-contract checks of recovered SCRIPT/LESSON -> five timing tasks."""
import unittest
from dataclasses import replace
from bie.director.script_plan import ScriptSegment, build_script_plan
from bie.director.voiceover_generation import generate_voiceover
from bie.director.emphasis_plan import plan_emphasis
from bie.director.speech_timing import utterances_from_script, estimate_speech, validate_speech_plan, align_reported_speech
from bie.director.pause_timing import PauseCue, build_pause_timing
from bie.director.emphasis_timing import EmphasisAnchor, build_emphasis_timing
from bie.director.scene_duration_fit import fit_scene_durations
from bie.director.wpm_adaptation import adapt_wpm
from timing_fixtures import inputs, speech, measured, empty_plans, target, load, cue, anchor


class TimingContractTests(unittest.TestCase):
    def test_grounded_director_to_timeline_end_to_end(self):
        text="A medium of exchange helps people trade."
        script=build_script_plan("lesson",[ScriptSegment("s10","trade","EXPLAIN",
            "Explain exchange",("book:p3",),("objective:exchange",))],"teacher-v1")
        draft=generate_voiceover("s10",[text,"unsupported addition"],{text:("book:p3",)})
        u=utterances_from_script(script,[draft],["s10"])
        s=estimate_speech(u,wpm=120)
        d=plan_emphasis([("concept:medium",1,.8,.8)])[0]
        p=build_pause_timing(s,[PauseCue("processing","s10",4,500,"Core definition",("book:p3",))])
        e=build_emphasis_timing(s,[EmphasisAnchor("medium","s10",1,4,d,("book:p3",))])
        f=fit_scene_durations(s,p,e)
        a=adapt_wpm(s,p,e,replace(load(.7,.4,.2),evidence_ids=("book:p3",)))
        events=a.candidate_scene_plan.scenes[0].events
        self.assertEqual(len([x for x in events if x.kind=="SPEECH"]),7)
        self.assertTrue(all(x.evidence_ids==("book:p3",) for x in events))
        self.assertTrue(all(x.objective_ids==("objective:exchange",) for x in events))
        self.assertEqual(s.utterances[0].utterance.script_fingerprint,script.fingerprint())
        self.assertIn("UNSUPPORTED_CLAIMS_WITHHELD",a.review_reasons)
        self.assertGreater(f.duration_ms,s.utterances[0].duration_ms)

    def test_known_legacy_blank_id_gap_blocked_at_new_boundary(self):
        # Invalid deserialized records must still be rejected at the TIME boundary.
        # The hardened producer now rejects these IDs before creating a plan.
        from bie.director.script_plan import ScriptPlan
        with self.assertRaises(ValueError):
            build_script_plan("l",[ScriptSegment(" ","s","explain","intent",(" ",),(" ",))],"v")
        script=ScriptPlan("l",(ScriptSegment(" ","s","explain","intent",(" ",),(" ",)),),"v")
        with self.assertRaises(ValueError):
            utterances_from_script(script,[],[" "])

    def test_policy_revision_invalidates_dependent_plans(self):
        s=speech(); p,e=empty_plans(s)
        updated=estimate_speech([x.utterance for x in s.utterances],replace(s.policy,version="new-policy"),120)
        with self.assertRaises(ValueError):
            fit_scene_durations(updated,p,e)

    def test_missing_grounded_voiceover_abstains_instead_of_timing_intent(self):
        script=build_script_plan("l",[ScriptSegment("u","s","EXPLAIN","planned explanation",("e",),("o",))],"v")
        draft=generate_voiceover("u",["unverified"],{})
        with self.assertRaises(ValueError):
            utterances_from_script(script,[draft],["u"])

    def test_all_words_once_across_multiple_utterances_with_adjacent_pauses(self):
        u=inputs()[0]
        s=estimate_speech([u,replace(u,utterance_id="second",segment_id="second")],wpm=120)
        p=build_pause_timing(s,[cue(4,100),replace(cue(0,200,"next"),utterance_id="second")])
        e=build_emphasis_timing(s)
        scene=fit_scene_durations(s,p,e).scenes[0]
        self.assertEqual(scene.duration_ms,4200)
        self.assertEqual(len(p.slots),1)
        self.assertEqual(p.slots[0].cue_ids,("next","p"))
        keys=[(x.utterance_id,x.word_index) for x in scene.events if x.kind=="SPEECH"]
        self.assertEqual(len(keys),8)
        self.assertEqual(len(set(keys)),8)

    def test_reported_audio_boundaries_do_not_change_through_full_stack(self):
        s=measured(); p=build_pause_timing(s,[cue(ms=800)]); e=build_emphasis_timing(s,[anchor()])
        a=adapt_wpm(s,p,e,load(1,1,1),[target(1)])
        self.assertEqual(a.candidate_speech,s)
        self.assertTrue(a.candidate_scene_plan.scenes[0].requires_audio_replan)
        self.assertEqual(a.candidate_scene_plan.duration_ms,2000)

    def test_adjacent_recorded_clip_silence_satisfies_one_shared_pause(self):
        first=measured().utterances[0]
        second=replace(first.utterance,utterance_id="second",segment_id="second")
        alignment=replace(first.alignment,utterance_fingerprint=second.fingerprint())
        s=align_reported_speech([first.utterance,second],[first.alignment,alignment])
        p=build_pause_timing(s,[cue(2,400),replace(cue(0,600,"next"),utterance_id="second")])
        self.assertEqual(len(p.slots),1)
        self.assertEqual(p.slots[0].existing_ms,600)
        self.assertFalse(p.requires_rerender)
        scene=fit_scene_durations(s,p,build_emphasis_timing(s)).scenes[0]
        self.assertEqual(scene.duration_ms,4000)
        self.assertEqual(sum(x.end_ms-x.start_ms for x in scene.events if x.cue_ids),600)

    def test_numeric_type_tampering_is_not_equal_to_validated_record(self):
        s=speech(); t=s.utterances[0]
        w=replace(t.words[0],start_ms=False)
        with self.assertRaises(ValueError):
            validate_speech_plan(replace(s,utterances=(replace(t,words=(w,)+t.words[1:]),)))

    def test_synthetic_duration_grid_conserves_timeline_and_rate_bounds(self):
        # Small deterministic property grid, not a learned/empirical benchmark.
        for count in (1,4,11):
            for rate in (80,137,200):
                s=speech(" ".join(["token"]*count),rate)
                p=build_pause_timing(s,[cue(0,111),cue(count,222,"tail")])
                e=build_emphasis_timing(s,[anchor(0,count,.7)])
                scene=fit_scene_durations(s,p,e).scenes[0]
                self.assertEqual(scene.duration_ms,scene.events[-1].end_ms)
                self.assertEqual(scene.duration_ms,sum(x.end_ms-x.start_ms for x in scene.events))
                self.assertTrue(all(x.end_ms>x.start_ms for x in scene.events))
                self.assertTrue(all(80<=x.effective_wpm<=200 for x in e.words))
