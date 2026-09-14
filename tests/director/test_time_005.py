import unittest
from dataclasses import replace
from bie.director.wpm_adaptation import *
from bie.director.speech_timing import estimate_speech
from bie.director.pause_timing import build_pause_timing
from bie.director.emphasis_timing import build_emphasis_timing
from timing_fixtures import speech, measured, empty_plans, cue, anchor, target, load, inputs


class WpmAdaptationTests(unittest.TestCase):
    def test_source_load_slowdown_needs_no_learner_profile(self):
        s=speech(); p,e=empty_plans(s)
        plain=adapt_wpm(s,p,e,load())
        dense=adapt_wpm(s,p,e,load(1,1,1))
        self.assertEqual(plain.selected_wpm,150)
        self.assertAlmostEqual(dense.selected_wpm,82.5)
        self.assertLess(dense.content_rate_ceiling,plain.content_rate_ceiling)

    def test_feasible_target_selects_bounded_rate(self):
        s=speech(); p,e=empty_plans(s)
        a=adapt_wpm(s,p,e,load(),[target(1.4)])
        self.assertEqual(a.status,"TARGET_FIT_ESTIMATED")
        self.assertGreater(a.selected_wpm,150)
        self.assertLessEqual(a.selected_wpm,200)
        self.assertLessEqual(a.candidate_scene_plan.duration_ms,1400)

    def test_impossible_budget_keeps_preferred_rate_and_all_words(self):
        s=speech(); p,e=empty_plans(s)
        a=adapt_wpm(s,p,e,load(),[target(.2)])
        self.assertEqual(a.status,"EXTEND_OR_SPLIT_REQUIRED")
        self.assertEqual(a.selected_wpm,a.preferred_wpm)
        self.assertEqual(len(a.candidate_speech.utterances[0].words),4)

    def test_pause_budget_is_not_consumed_by_speedup(self):
        s=speech(); p=build_pause_timing(s,[cue(ms=2000)]); e=build_emphasis_timing(s)
        a=adapt_wpm(s,p,e,load(),[target(1)])
        self.assertEqual(a.status,"EXTEND_OR_SPLIT_REQUIRED")
        self.assertEqual(a.candidate_pauses.slots[0].additional_ms,2000)

    def test_rebuilds_emphasis_and_lineage_after_rate_change(self):
        s=speech(); p=build_pause_timing(s,[cue()]); e=build_emphasis_timing(s,[anchor()])
        a=adapt_wpm(s,p,e,load(),[target(2)])
        self.assertEqual(a.status,"TARGET_FIT_ESTIMATED")
        self.assertEqual(a.candidate_emphasis.speech_fingerprint,a.candidate_speech.fingerprint())
        self.assertEqual(a.candidate_pauses.speech_fingerprint,a.candidate_speech.fingerprint())
        self.assertNotEqual(a.input_speech_fingerprint,a.candidate_speech.fingerprint())
        self.assertEqual(a.candidate_emphasis.anchors,e.anchors)

    def test_recorded_audio_never_silently_rescaled(self):
        s=measured(); p,e=empty_plans(s)
        a=adapt_wpm(s,p,e,load(),[target(.1)])
        self.assertEqual(a.status,"AUDIO_REPLAN_REQUIRED")
        self.assertIsNone(a.selected_wpm)
        self.assertEqual(a.candidate_speech,s)
        self.assertEqual(a.candidate_scene_plan.duration_ms,2000)

    def test_invalid_load_and_evidence(self):
        s=speech(); p,e=empty_plans(s)
        for row in (load(True),load(-1),load(float("nan")),load(notation=1.1),
                    replace(load(),evidence_ids=("outside",))):
            with self.subTest(row=row),self.assertRaises(ValueError):
                adapt_wpm(s,p,e,row)

    def test_multiple_scene_constraints_each_checked(self):
        u=inputs()[0]
        s=estimate_speech([u,replace(u,utterance_id="b",scene_id="second",text="Brief text.")])
        p,e=empty_plans(s)
        a=adapt_wpm(s,p,e,load(),[target(1.4),target(.65,"second")])
        self.assertEqual(a.status,"TARGET_FIT_ESTIMATED")
        self.assertTrue(all(x.duration_ms<=x.target_ms for x in a.candidate_scene_plan.scenes))

    def test_dense_content_ceiling_can_require_extension(self):
        s=speech(); p,e=empty_plans(s)
        self.assertEqual(adapt_wpm(s,p,e,load(),[target(1.4)]).status,"TARGET_FIT_ESTIMATED")
        dense=adapt_wpm(s,p,e,load(1,1,1),[target(1.4)])
        self.assertEqual(dense.status,"EXTEND_OR_SPLIT_REQUIRED")
        self.assertLessEqual(dense.selected_wpm,dense.content_rate_ceiling)

    def test_repeated_adaptation_does_not_accumulate_slowdown(self):
        s=speech(); p,e=empty_plans(s)
        a=adapt_wpm(s,p,e,load(.6,.2,.5))
        b=adapt_wpm(a.candidate_speech,a.candidate_pauses,a.candidate_emphasis,load(.6,.2,.5))
        self.assertEqual(a.selected_wpm,b.selected_wpm)
        self.assertEqual(a.candidate_speech,b.candidate_speech)

    def test_generator_targets_and_policy_fingerprints(self):
        s=speech(); p,e=empty_plans(s)
        a=adapt_wpm(s,p,e,load(),(x for x in [target(1.4)]))
        b=adapt_wpm(s,p,e,load(),[target(1.4)])
        self.assertEqual(a.fingerprint(),b.fingerprint())
        c=adapt_wpm(s,p,e,load(),[target(1.4)],WpmAdaptationPolicy(version="v2"))
        self.assertNotEqual(b.fingerprint(),c.fingerprint())

    def test_acceptance_and_uncertainty_remain_open(self):
        s=speech(); p,e=empty_plans(s)
        a=adapt_wpm(s,p,e,load(),[target(1.61)])
        self.assertIn("CONTENT_LOAD_RATE_POLICY_UNCALIBRATED",a.review_reasons)
        self.assertFalse(a.candidate_speech.audio_verified)
        self.assertTrue(a.candidate_scene_plan.requires_review)
