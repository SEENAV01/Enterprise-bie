import unittest
from dataclasses import replace
from bie.director.repetition_detection import (RepeatPurpose, RepetitionPolicy,
    sentence_spans, repetition_qa, validate_repetition_report)
from bie.pedagogy.repetition_policy import repetition_policy
from qa_fixtures import case, codes

TEXT = "A triangle has exactly three straight sides."


class RepetitionTests(unittest.TestCase):
    def purpose(self, c, mode="RECAP", **kwargs):
        spans = sentence_spans(c.snapshot)
        return RepeatPurpose(spans[0], spans[1], mode, "Revisit the grounded objective", ("e1",), ("o1",), **kwargs)

    def test_exact_duplicate_across_utterances_is_candidate(self):
        c = case((TEXT, TEXT), shared=True)
        r = repetition_qa(c.snapshot)
        self.assertIn("EXACT_REPETITION", codes(r)); self.assertEqual(dict(r.measurements)["candidate_pairs"], 1)

    def test_duplicate_inside_one_utterance_detected(self):
        c = case((TEXT + " " + TEXT,))
        self.assertIn("EXACT_REPETITION", codes(repetition_qa(c.snapshot)))

    def test_no_duplicate_passes_scoped_heuristic(self):
        c = case((TEXT, "Money can serve as a medium of exchange."))
        r = repetition_qa(c.snapshot); self.assertEqual(r.status, "CHECKS_PASSED"); self.assertFalse(r.accepted)

    def test_explicit_recap_is_retained_and_never_rewrites(self):
        c = case((TEXT, TEXT), shared=True); before = c.snapshot.fingerprint()
        r = repetition_qa(c.snapshot, (self.purpose(c),))
        self.assertIn("PURPOSEFUL_REPETITION_RETAINED", codes(r)); self.assertEqual(r.status, "CHECKS_PASSED")
        self.assertEqual(c.snapshot.fingerprint(), before)

    def test_retrieval_label_does_not_exempt_identical_exposition(self):
        c = case((TEXT, TEXT), shared=True)
        self.assertIn("ACTIVE_PRACTICE_NOT_DEMONSTRATED", codes(repetition_qa(c.snapshot, (self.purpose(c, "RETRIEVAL"),))))

    def test_active_retrieval_can_be_retained(self):
        c = case((TEXT, "Explain why a triangle has exactly three straight sides?"), shared=True)
        r = repetition_qa(c.snapshot, (self.purpose(c, "RETRIEVAL"),), RepetitionPolicy(near_duplicate_threshold=.75))
        self.assertIn("PURPOSEFUL_REPETITION_RETAINED", codes(r))

    def test_repeated_active_question_can_support_spaced_retrieval(self):
        text = "Why does a triangle have three straight sides?"
        c = case((text, text), shared=True)
        p = self.purpose(c, "RETRIEVAL", pedagogy_decision=repetition_policy(.95, True, 0))
        self.assertIn("PURPOSEFUL_REPETITION_RETAINED", codes(repetition_qa(c.snapshot, (p,))))

    def test_negative_sign_change_is_not_normalized_away(self):
        c = case(("The current measured value is exactly 12 units.", "The current measured value is exactly -12 units."), shared=True)
        self.assertIn("REPEATED_TEXT_FACTUAL_DIFFERENCE", codes(repetition_qa(c.snapshot, (self.purpose(c),))))

    def test_changed_currency_and_units_cannot_get_unqualified_recap_pass(self):
        for first, second in (("The current measured value is exactly $12.", "The current measured value is exactly €12."),
                              ("The current measured length is exactly 12 cm.", "The current measured length is exactly 12 m.")):
            c = case((first, second), shared=True)
            self.assertEqual(repetition_qa(c.snapshot, (self.purpose(c),)).status, "REVIEW_REQUIRED")

    def test_changed_numbers_require_factual_review_even_for_recap(self):
        c = case(("The current measured length is exactly 12 cm.", "The current measured length is exactly 15 cm."), shared=True)
        r = repetition_qa(c.snapshot, (self.purpose(c),))
        self.assertIn("REPEATED_TEXT_FACTUAL_DIFFERENCE", codes(r)); self.assertNotIn("PURPOSEFUL_REPETITION_RETAINED", codes(r))

    def test_negation_difference_preserved(self):
        c = case((TEXT, "A triangle does not have exactly three straight sides."), shared=True)
        self.assertIn("REPEATED_TEXT_FACTUAL_DIFFERENCE", codes(repetition_qa(c.snapshot, policy=RepetitionPolicy(near_duplicate_threshold=.7))))

    def test_pedagogy_retrieval_only_conflicts_with_repeated_lecture(self):
        c = case((TEXT, TEXT), shared=True)
        p = self.purpose(c, pedagogy_decision=repetition_policy(.95, True, 0))
        self.assertIn("PEDAGOGY_REPEAT_CONFLICT", codes(repetition_qa(c.snapshot, (p,))))

    def test_decimal_values_are_one_sentence_and_preserved_tokens(self):
        c = case(("The current measured length is exactly 1.2 cm.", "The current measured length is exactly 1.5 cm."), shared=True)
        self.assertEqual(len(sentence_spans(c.snapshot)), 2)
        self.assertIn("REPEATED_TEXT_FACTUAL_DIFFERENCE", codes(repetition_qa(c.snapshot)))

    def test_unrelated_evidence_invalidates_repeat_exception(self):
        c = case((TEXT, TEXT))
        with self.assertRaises(ValueError): repetition_qa(c.snapshot, (self.purpose(c),))

    def test_stale_reverse_and_duplicate_purpose_rejected(self):
        c = case((TEXT, TEXT), shared=True); p = self.purpose(c)
        for purposes in ((replace(p, first=p.repeated, repeated=p.first),), (p, p), (replace(p, first=replace(p.first, utterance_fingerprint="sha256:"+"0"*64)),)):
            with self.assertRaises(ValueError): repetition_qa(c.snapshot, purposes)

    def test_language_and_short_text_limits_explicit(self):
        c = case(("यह एक उदाहरण है।",), language="hi")
        self.assertIn("LANGUAGE_SIMILARITY_UNCALIBRATED", codes(repetition_qa(c.snapshot)))
        c = case(("Yes.", "Yes."), shared=True)
        self.assertEqual(dict(repetition_qa(c.snapshot).measurements)["candidate_pairs"], 0)

    def test_report_replay_and_threshold_validation(self):
        c = case((TEXT, TEXT), shared=True); r = repetition_qa(c.snapshot)
        self.assertEqual(validate_repetition_report(r, c.snapshot), r)
        with self.assertRaises(ValueError): validate_repetition_report(r, c.snapshot, (self.purpose(c),))
        for p in (RepetitionPolicy(minimum_words=True), RepetitionPolicy(near_duplicate_threshold=float("nan"))):
            with self.assertRaises(ValueError): repetition_qa(c.snapshot, policy=p)
