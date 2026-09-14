import unittest
from dataclasses import replace
from bie.director.pause_timing import *
from timing_fixtures import speech, measured, cue


class PauseTimingTests(unittest.TestCase):
    def test_estimated_pause_adds_explicit_duration(self):
        p=build_pause_timing(speech(),[cue()])
        self.assertEqual(p.slots[0].additional_ms,400)
        self.assertFalse(p.requires_rerender)

    def test_coincident_cues_use_max_not_sum(self):
        p=build_pause_timing(speech(),[cue(ms=300),cue(ms=600,cid="p2")])
        self.assertEqual(p.slots[0].additional_ms,600)
        self.assertEqual(p.slots[0].cue_ids,("p","p2"))

    def test_existing_audio_gap_counted_once(self):
        p=build_pause_timing(measured(),[cue(ms=300)])
        self.assertEqual(p.slots[0].existing_ms,400)
        self.assertEqual(p.slots[0].additional_ms,0)
        self.assertFalse(p.requires_rerender)

    def test_recorded_gap_shortfall_preserves_audio(self):
        p=build_pause_timing(measured(),[cue(ms=700)])
        self.assertEqual(p.slots[0].shortfall_ms,300)
        self.assertEqual(p.slots[0].additional_ms,0)
        self.assertTrue(p.requires_rerender)

    def test_leading_and_trailing_boundaries(self):
        p=build_pause_timing(measured(),[cue(0,100),cue(2,500,"tail")])
        self.assertEqual([x.existing_ms for x in p.slots],[100,500])
        self.assertFalse(p.requires_rerender)

    def test_unknown_outside_and_blank_grounding(self):
        for c in (replace(cue(),utterance_id="bad"),cue(5),cue(-1),
                  replace(cue(),evidence_ids=(" ",)),replace(cue(),evidence_ids=("x",))):
            with self.subTest(c=c),self.assertRaises(ValueError):
                build_pause_timing(speech(),[c])

    def test_invalid_duration_and_duplicate_cue(self):
        for value in (0,-1,True,1.2,float("nan")):
            with self.subTest(value=value),self.assertRaises(ValueError):
                build_pause_timing(speech(),[cue(ms=value)])
        with self.assertRaises(ValueError):
            build_pause_timing(speech(),[cue(),cue()])

    def test_generator_and_input_order_determinism(self):
        rows=[cue(3,200,"late"),cue(1,300,"early")]
        a=build_pause_timing(speech(),(x for x in rows))
        b=build_pause_timing(speech(),reversed(rows))
        self.assertEqual(a.fingerprint(),b.fingerprint())

    def test_stale_or_edited_pause_rejected(self):
        s=speech(); p=build_pause_timing(s,[cue()])
        with self.assertRaises(ValueError):
            validate_pause_plan(speech(wpm=150),p)
        with self.assertRaises(ValueError):
            validate_pause_plan(s,replace(p,slots=()))
