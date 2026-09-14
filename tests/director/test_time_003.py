import unittest
from dataclasses import replace
from bie.director.emphasis_timing import *
from timing_fixtures import speech, measured, anchor


class EmphasisTimingTests(unittest.TestCase):
    def test_local_emphasis_math(self):
        p=build_emphasis_timing(speech(),[anchor()])
        self.assertEqual(p.words[0].effective_wpm,90)
        self.assertEqual(p.words[0].additional_ms,167)
        self.assertEqual(p.words[0].concept_id,"concept-exchange")

    def test_unanchored_words_unchanged(self):
        p=build_emphasis_timing(speech(),[anchor(1,3)])
        self.assertEqual([w.word_index for w in p.words],[1,2])

    def test_zero_strength_does_not_stretch_rounding(self):
        p=build_emphasis_timing(speech(wpm=137),[anchor(strength=0)])
        self.assertEqual(p.words[0].additional_ms,0)

    def test_floor_prevents_unbounded_slowdown(self):
        p=build_emphasis_timing(speech(wpm=80),[anchor()])
        self.assertEqual(p.words[0].effective_wpm,80)
        self.assertEqual(p.words[0].additional_ms,0)
        self.assertTrue(p.words[0].floor_limited)
        self.assertTrue(p.review_reasons)

    def test_overlap_requires_explicit_resolution(self):
        with self.assertRaises(ValueError):
            build_emphasis_timing(speech(),[anchor(0,2),anchor(1,3,aid="overlap")])

    def test_invalid_spans_and_grounding(self):
        for a in (anchor(-1,2),anchor(2,2),anchor(0,5),anchor(True,2),
                  replace(anchor(),evidence_ids=("unknown",)),replace(anchor(),utterance_id="missing")):
            with self.subTest(a=a),self.assertRaises(ValueError):
                build_emphasis_timing(speech(),[a])

    def test_invalid_strength_and_policy(self):
        for value in (True,-1,1.1,float("nan"),float("inf")):
            with self.subTest(value=value),self.assertRaises(ValueError):
                build_emphasis_timing(speech(),[anchor(strength=value)])
        with self.assertRaises(ValueError):
            build_emphasis_timing(speech(),policy=EmphasisPolicy(maximum_slowdown=1))

    def test_recorded_emphasis_cannot_retime_audio(self):
        p=build_emphasis_timing(measured(),[anchor()])
        self.assertEqual(p.words[0].additional_ms,0)
        self.assertIsNone(p.words[0].effective_wpm)
        self.assertIn("REPORTED_EMPHASIS_REQUIRES_AUDIO_QA",p.review_reasons)

    def test_fingerprint_tracks_concept_and_order_is_canonical(self):
        a,b=anchor(),anchor(3,4,aid="last")
        first=build_emphasis_timing(speech(),[b,a])
        second=build_emphasis_timing(speech(),(x for x in [a,b]))
        self.assertEqual(first.fingerprint(),second.fingerprint())
        different=replace(a,decision=replace(a.decision,concept_id="other"))
        self.assertNotEqual(build_emphasis_timing(speech(),[a]).fingerprint(),
                            build_emphasis_timing(speech(),[different]).fingerprint())

    def test_stale_or_edited_plan_rejected(self):
        s=speech(); p=build_emphasis_timing(s,[anchor()])
        with self.assertRaises(ValueError):
            validate_emphasis_plan(speech(wpm=160),p)
        with self.assertRaises(ValueError):
            validate_emphasis_plan(s,replace(p,words=()))
