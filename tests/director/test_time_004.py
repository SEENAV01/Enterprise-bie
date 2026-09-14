import unittest
from dataclasses import replace
from bie.director.scene_duration_fit import *
from bie.director.pause_timing import build_pause_timing
from bie.director.emphasis_timing import build_emphasis_timing
from bie.director.speech_timing import estimate_speech
from timing_fixtures import speech, measured, cue, anchor, target, empty_plans, inputs


class SceneDurationTests(unittest.TestCase):
    def test_duration_conservation_with_pause_and_emphasis(self):
        s=speech(); p=build_pause_timing(s,[cue()]); e=build_emphasis_timing(s,[anchor()])
        f=fit_scene_durations(s,p,e,[target(3)])
        scene=f.scenes[0]
        self.assertEqual(scene.duration_ms,2567)
        self.assertEqual(scene.speech_and_recorded_gaps_ms,2000)
        self.assertEqual(scene.additional_pause_ms,400)
        self.assertEqual(scene.additional_emphasis_ms,167)
        self.assertEqual(scene.status,"WITHIN_TARGET")
        self.assertEqual(sum(x.end_ms-x.start_ms for x in scene.events),2567)
        self.assertEqual(scene.events[0].start_ms,0)
        self.assertEqual(scene.events[-1].end_ms,2567)
        for left,right in zip(scene.events,scene.events[1:]):
            self.assertEqual(left.end_ms,right.start_ms)

    def test_no_arbitrary_scene_duration_cap(self):
        s=speech(" ".join(["word"]*600)); p,e=empty_plans(s)
        f=fit_scene_durations(s,p,e)
        self.assertEqual(f.duration_ms,300000)
        self.assertEqual(f.scenes[0].status,"NO_TARGET")

    def test_overflow_suggests_extension_or_split_preserving_words(self):
        s=speech(); p,e=empty_plans(s)
        for seconds,status in ((1.8,"EXTEND"),(1,"SPLIT_OR_EXTEND")):
            f=fit_scene_durations(s,p,e,[target(seconds)])
            self.assertEqual(f.scenes[0].status,status)
            self.assertEqual(f.duration_ms,2000)
            self.assertEqual(len(f.scenes[0].events),4)

    def test_recorded_gaps_preserved_and_pause_not_double_counted(self):
        s=measured(); p=build_pause_timing(s,[cue()]); e=build_emphasis_timing(s,[anchor()])
        scene=fit_scene_durations(s,p,e).scenes[0]
        self.assertEqual(scene.duration_ms,2000)
        self.assertEqual(sum(x.end_ms-x.start_ms for x in scene.events if x.kind=="RECORDED_GAP"),1000)
        self.assertEqual([(x.start_ms,x.end_ms) for x in scene.events if x.kind=="SPEECH"],[(100,600),(1000,1500)])

    def test_recorded_pause_shortfall_needs_replan_even_when_budget_fits(self):
        s=measured(); p=build_pause_timing(s,[cue(ms=900)]); e=build_emphasis_timing(s)
        scene=fit_scene_durations(s,p,e,[target(3)]).scenes[0]
        self.assertEqual(scene.status,"WITHIN_TARGET")
        self.assertTrue(scene.requires_audio_replan)
        self.assertEqual(scene.duration_ms,2000)

    def test_estimate_margin_is_planning_range_not_confidence_certificate(self):
        s=speech(); p,e=empty_plans(s)
        scene=fit_scene_durations(s,p,e,[target(2.1)]).scenes[0]
        self.assertEqual(scene.planning_upper_ms,2400)
        self.assertIn("TARGET_WITHIN_ESTIMATE_UNCERTAINTY",scene.review_reasons)

    def test_multiple_scenes_keep_order_and_local_zero_origin(self):
        u=inputs()[0]
        s=estimate_speech([replace(u,scene_id="z"),replace(u,utterance_id="b",scene_id="a")])
        p,e=empty_plans(s); f=fit_scene_durations(s,p,e)
        self.assertEqual([x.scene_id for x in f.scenes],["z","a"])
        self.assertTrue(all(x.events[0].start_ms==0 for x in f.scenes))

    def test_bad_and_unknown_targets_rejected(self):
        s=speech(); p,e=empty_plans(s)
        for t in (target(True),target(0),target(float("inf")),target(float("nan")),target(2,"other")):
            with self.subTest(t=t),self.assertRaises(ValueError):
                fit_scene_durations(s,p,e,[t])
        with self.assertRaises(ValueError):
            fit_scene_durations(s,p,e,[target(2),target(2)])

    def test_target_generators_and_target_policy_provenance(self):
        s=speech(); p,e=empty_plans(s)
        a=fit_scene_durations(s,p,e,(x for x in [target(2)]))
        b=fit_scene_durations(s,p,e,[target(2)])
        self.assertEqual(a.fingerprint(),b.fingerprint())
        c=fit_scene_durations(s,p,e,[target(2)],SceneFitPolicy(version="changed/2"))
        self.assertNotEqual(b.fingerprint(),c.fingerprint())

    def test_cross_revision_plans_fail_before_composition(self):
        s=speech(); p,e=empty_plans(s)
        with self.assertRaises(ValueError):
            fit_scene_durations(speech(wpm=170),p,e)
