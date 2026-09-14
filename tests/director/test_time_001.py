import unittest
from dataclasses import replace
from bie.director.timing_contract import TimingPolicy
from bie.director.speech_timing import *
from bie.director.script_plan import ScriptSegment, build_script_plan
from bie.director.voiceover_generation import VoiceoverDraft, generate_voiceover
from timing_fixtures import inputs, speech, measured


class SpeechTimingTests(unittest.TestCase):
    def test_exact_word_math_and_character_anchors(self):
        plan = speech()
        self.assertEqual(plan.utterances[0].duration_ms, 2000)
        self.assertEqual([(w.start_ms, w.end_ms) for w in plan.utterances[0].words],
                         [(0,500),(500,1000),(1000,1500),(1500,2000)])
        for w in plan.utterances[0].words:
            self.assertEqual(plan.utterances[0].utterance.text[w.word.start_char:w.word.end_char], w.word.text)

    def test_explicit_narrative_order_survives_sorted_script_ids(self):
        segments = [ScriptSegment(x, x, "EXPLAIN", "intent", ("e",), ("o",)) for x in ("z", "a")]
        script = build_script_plan("l", segments, "v")
        drafts = [generate_voiceover(x, ["Real words."], {"Real words.": ("e",)}) for x in ("a", "z")]
        u = utterances_from_script(script, (d for d in drafts), (x for x in ("z", "a")))
        self.assertEqual([x.scene_id for x in u], ["z", "a"])
        self.assertEqual(u[0].text, "Real words.")

    def test_generators_and_fingerprints(self):
        u = inputs()
        a = estimate_speech(x for x in u)
        self.assertEqual(a, estimate_speech(u))
        self.assertEqual(a.fingerprint(), estimate_speech(u).fingerprint())
        self.assertNotEqual(a.fingerprint(), estimate_speech(u, wpm=160).fingerprint())

    def test_bad_rates_and_policy(self):
        for bad in (True, False, float("nan"), float("inf"), 0, -1, 201):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                estimate_speech(inputs(), wpm=bad)
        with self.assertRaises(ValueError):
            estimate_speech(inputs(), TimingPolicy(estimate_margin=float("nan")))

    def test_estimate_is_not_audio_acceptance(self):
        p = speech()
        self.assertEqual(p.basis, "ESTIMATED_WPM")
        self.assertFalse(p.audio_verified)
        self.assertTrue(p.requires_review)

    def test_numeric_and_language_realization_review(self):
        p = speech("x = 2 + 3")
        self.assertIn("NUMERIC_OR_SYMBOLIC_SPOKEN_REALIZATION_REQUIRED", p.review_reasons)
        u = replace(inputs()[0], language="hi")
        self.assertIn("LANGUAGE_TOKENIZATION_UNCALIBRATED", estimate_speech([u]).review_reasons)
        with self.assertRaises(ValueError):
            estimate_speech([replace(u, text="... =")])

    def test_bad_grounding_and_unordered_inputs_rejected(self):
        u = inputs()[0]
        for field, value in (("evidence_ids",(" ",)), ("objective_ids",()), ("utterance_id"," "),
                             ("script_fingerprint","unknown"), ("evidence_ids",["e"])):
            with self.subTest(field=field), self.assertRaises(ValueError):
                estimate_speech([replace(u, **{field:value})])
        with self.assertRaises(ValueError):
            estimate_speech({u})

    def test_duplicate_and_revisited_scenes_rejected(self):
        u = inputs()[0]
        with self.assertRaises(ValueError):
            estimate_speech([u,u])
        with self.assertRaises(ValueError):
            estimate_speech([u,replace(u,utterance_id="b",scene_id="b"),replace(u,utterance_id="c")])

    def test_script_revision_mixing_rejected(self):
        u = inputs()[0]
        with self.assertRaises(ValueError):
            estimate_speech([u,replace(u,utterance_id="b",script_fingerprint="sha256:"+"b"*64)])

    def test_adapter_checks_coverage_and_source_subset(self):
        s = build_script_plan("l", [ScriptSegment("u","s","EXPLAIN","intent",("e",),("o",))], "v")
        draft = VoiceoverDraft("u","spoken",("outside",),(),False)
        with self.assertRaises(ValueError):
            utterances_from_script(s,[draft],["u"])
        with self.assertRaises(ValueError):
            utterances_from_script(s,[],["u"])

    def test_upstream_unsupported_claim_review_survives(self):
        s = build_script_plan("l", [ScriptSegment("u","s","EXPLAIN","intent",("e",),("o",))], "v")
        d = generate_voiceover("u",["supported","invented"],{"supported":("e",)})
        p = estimate_speech(utterances_from_script(s,[d],["u"]))
        self.assertEqual(p.utterances[0].utterance.text,"supported")
        self.assertIn("UNSUPPORTED_CLAIMS_WITHHELD",p.review_reasons)

    def test_reported_audio_is_validated_but_not_certified(self):
        p=measured()
        self.assertEqual(p.utterances[0].duration_ms,2000)
        self.assertIsNone(p.utterances[0].wpm)
        self.assertFalse(p.audio_verified)
        self.assertEqual(validate_speech_plan(p),p)

    def test_alignment_binds_text_voice_evidence(self):
        t=measured().utterances[0]
        for u in (replace(t.utterance,text="Other words."),replace(t.utterance,voice_id="other"),
                  replace(t.utterance,evidence_ids=("new",))):
            with self.subTest(u=u),self.assertRaises(ValueError):
                align_reported_speech([u],[t.alignment])

    def test_alignment_overlap_bounds_and_hashes(self):
        t=measured().utterances[0]
        for field,value in (("word_intervals_ms",((0,800),(700,900))),
                            ("word_intervals_ms",((0,500),(700,2001))),
                            ("word_intervals_ms",((True,500),(700,900))),
                            ("word_intervals_ms",((0,500),)), ("audio_sha256","fake")):
            with self.subTest(field=field),self.assertRaises(ValueError):
                align_reported_speech([t.utterance],[replace(t.alignment,**{field:value})])

    def test_edited_result_rejected_at_downstream_boundary(self):
        p=speech()
        t=replace(p.utterances[0],duration_ms=1)
        with self.assertRaises(ValueError):
            validate_speech_plan(replace(p,utterances=(t,)))
        with self.assertRaises(ValueError):
            validate_speech_plan(replace(p,review_reasons=(),audio_verified=True))
