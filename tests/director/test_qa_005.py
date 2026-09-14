import unittest
from dataclasses import replace
from bie.director.qa_contract import bind_span
from bie.director.assessment_prompts import make_assessment_prompt
from bie.director.age_level_qa import (AudienceTarget, AudiencePolicy, TermRequirement,
    ContentAdvisory, LEVELS, age_level_qa, validate_age_level_report)
from qa_fixtures import case, codes

TARGET = AudienceTarget(10, 12, 1, LEVELS, "Controlled curriculum policy, not calibrated age prediction")
REVIEWED = AudiencePolicy(annotation_review_completed=True)


class AudienceTests(unittest.TestCase):
    def test_source_generation_without_audience_or_profile_remains_possible(self):
        c = case(); r = age_level_qa(c.snapshot)
        self.assertIn("AUDIENCE_TARGET_UNSPECIFIED", codes(r)); self.assertEqual(r.status, "REVIEW_REQUIRED")

    def test_missing_annotation_review_is_never_silent_pass(self):
        c = case(); self.assertIn("AUDIENCE_ANNOTATIONS_UNREVIEWED", codes(age_level_qa(c.snapshot, TARGET)))

    def test_reviewed_declared_policy_passes_only_scoped_checks(self):
        c = case(); r = age_level_qa(c.snapshot, TARGET, policy=REVIEWED)
        self.assertEqual(r.status, "CHECKS_PASSED"); self.assertFalse(r.accepted)

    def test_advanced_term_needs_scaffold_at_first_use(self):
        c = case(("Entropy describes a quantity in this model.",))
        t = TermRequirement("entropy", 3, ("e1",))
        self.assertIn("ADVANCED_TERM_WITHOUT_PRIOR_SCAFFOLD", codes(age_level_qa(c.snapshot, TARGET, (t,), policy=REVIEWED)))
        t = replace(t, definition=bind_span(c.snapshot, "u1"))
        self.assertIn("DECLARED_TERM_SCAFFOLD", codes(age_level_qa(c.snapshot, TARGET, (t,), policy=REVIEWED)))

    def test_later_definition_does_not_cover_earlier_use(self):
        c = case(("Entropy appears before any definition.", "Entropy means the declared model quantity."), shared=True)
        t = TermRequirement("entropy", 3, ("e1",), bind_span(c.snapshot, "u2"))
        self.assertIn("ADVANCED_TERM_WITHOUT_PRIOR_SCAFFOLD", codes(age_level_qa(c.snapshot, TARGET, (t,), policy=REVIEWED)))

    def test_term_matching_is_case_insensitive_and_word_bounded(self):
        c = case(("A triangle has straight sides.",))
        with self.assertRaises(ValueError): age_level_qa(c.snapshot, TARGET, (TermRequirement("angle", 3, ("e1",)),))
        with self.assertRaises(ValueError): age_level_qa(c.snapshot, TARGET, (TermRequirement("triangle", 3, ("e1",)), TermRequirement("Triangle", 2, ("e1",))))

    def test_definition_must_name_term_and_match_lineage(self):
        c = case(("Entropy appears here. A separate idea follows.",))
        start = c.snapshot.utterances[0].text.index("A separate")
        t = TermRequirement("entropy", 3, ("e1",), bind_span(c.snapshot, "u1", start))
        with self.assertRaises(ValueError): age_level_qa(c.snapshot, TARGET, (t,))
        with self.assertRaises(ValueError): age_level_qa(c.snapshot, TARGET, (replace(t, evidence_ids=("other",), definition=None),))

    def test_age_advisory_checks_youngest_audience_not_oldest(self):
        c = case(); a = ContentAdvisory("a1", bind_span(c.snapshot, "u1"), "MATURE_THEME", 11, "Controlled policy fixture")
        r = age_level_qa(c.snapshot, TARGET, advisories=(a,), policy=REVIEWED)
        self.assertIn("CONTENT_OUTSIDE_DECLARED_AGE_POLICY", codes(r)); self.assertEqual(r.status, "BLOCKED")
        self.assertNotIn("CONTENT_OUTSIDE_DECLARED_AGE_POLICY", codes(age_level_qa(c.snapshot, replace(TARGET, minimum_age=11), advisories=(a,), policy=REVIEWED)))

    def test_content_span_must_be_current(self):
        c = case(); a = ContentAdvisory("a1", replace(bind_span(c.snapshot, "u1"), utterance_fingerprint="sha256:"+"0"*64), "MATURE_THEME", 11, "policy")
        with self.assertRaises(ValueError): age_level_qa(c.snapshot, TARGET, advisories=(a,))

    def test_higher_order_assessment_allowed_for_young_target(self):
        c = case(); a = make_assessment_prompt("o1", "CREATE", "triangles", ("e1",))
        r = age_level_qa(c.snapshot, replace(TARGET, minimum_age=6, maximum_age=8), assessments=(a,), policy=REVIEWED)
        self.assertEqual(r.status, "CHECKS_PASSED")

    def test_explicit_cognitive_policy_and_assessment_lineage_checked(self):
        c = case(); a = make_assessment_prompt("o1", "CREATE", "triangles", ("e1",))
        r = age_level_qa(c.snapshot, replace(TARGET, allowed_assessment_levels=("UNDERSTAND",)), assessments=(a,), policy=REVIEWED)
        self.assertIn("ASSESSMENT_OUTSIDE_CURRICULUM_POLICY", codes(r))
        r = age_level_qa(c.snapshot, TARGET, assessments=(replace(a, objective_id="other"),), policy=REVIEWED)
        self.assertIn("ASSESSMENT_OUTSIDE_SCRIPT_LINEAGE", codes(r))

    def test_long_sentence_is_review_heuristic_not_grade_or_truncation(self):
        c = case(("This sentence deliberately contains several words to exceed a small declared threshold.",))
        before = c.snapshot.fingerprint()
        r = age_level_qa(c.snapshot, TARGET, policy=replace(REVIEWED, maximum_sentence_words=5))
        self.assertIn("SENTENCE_LOAD_REVIEW", codes(r)); self.assertEqual(c.snapshot.fingerprint(), before)

    def test_unknown_language_keeps_review(self):
        c = case(("यह एक उदाहरण है।",), language="hi")
        self.assertIn("AUDIENCE_LANGUAGE_UNCALIBRATED", codes(age_level_qa(c.snapshot, TARGET, policy=REVIEWED)))

    def test_decimal_sentence_and_unpunctuated_tail_are_not_lost(self):
        c = case(("The measured value is 1.5 units and this sentence continues without punctuation",))
        r = age_level_qa(c.snapshot, TARGET, policy=replace(REVIEWED, maximum_sentence_words=7))
        self.assertEqual(dict(r.measurements)["long_sentence_candidates"], 1)

    def test_invalid_target_boolean_threshold_and_edited_report_rejected(self):
        c = case()
        for t in (replace(TARGET, minimum_age=True), replace(TARGET, maximum_age=5)):
            with self.assertRaises(ValueError): age_level_qa(c.snapshot, t)
        with self.assertRaises(ValueError): age_level_qa(c.snapshot, TARGET, policy=replace(REVIEWED, maximum_sentence_words=True))
        r = age_level_qa(c.snapshot, TARGET, policy=REVIEWED)
        self.assertEqual(validate_age_level_report(r, c.snapshot, TARGET, policy=REVIEWED), r)
        with self.assertRaises(ValueError): validate_age_level_report(r, c.snapshot, replace(TARGET, level_rank=2), policy=REVIEWED)
