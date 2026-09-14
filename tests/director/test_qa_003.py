import unittest
from dataclasses import replace
from bie.director.qa_contract import bind_span
from bie.director.lesson_architecture_contract import LessonArchitecture, LessonSceneIntent
from bie.director.transition_strategy import Transition
from bie.director.script_coherence_qa import (DiscourseBeat, NarratedTransition,
    coherence_qa, validate_coherence_report)
from qa_fixtures import case, codes


def architecture(c, parents=()):
    scenes = []
    for sid in dict.fromkeys(u.scene_id for u in c.snapshot.utterances):
        evidence = tuple(sorted({e for u in c.snapshot.utterances if u.scene_id == sid for e in u.evidence_ids}))
        scenes.append(LessonSceneIntent(sid, "EXPLAIN", ("o1",), evidence, dict(parents).get(sid, ())))
    return LessonArchitecture("lesson1", "Controlled lesson", tuple(scenes), ("o1",), ("source1",), "fixture/1")


def beats(c):
    return tuple(DiscourseBeat(u.utterance_id, u.fingerprint()) for u in c.snapshot.utterances)


class CoherenceTests(unittest.TestCase):
    def test_declared_single_scene_structural_scope_passes(self):
        c = case(); r = coherence_qa(c.snapshot, architecture(c), beats(c))
        self.assertEqual(r.status, "CHECKS_PASSED"); self.assertFalse(r.accepted)

    def test_original_architecture_cycle_is_detected_without_mutation(self):
        c = case(("One concept starts here.", "Another concept follows here."), scene_ids=("s1", "s2"))
        a = architecture(c, (("s1", ("s2",)), ("s2", ("s1",))))
        before = a.fingerprint(); r = coherence_qa(c.snapshot, a, beats(c))
        self.assertTrue({"SCENE_PARENT_CYCLE", "PARENT_NOT_BEFORE_CHILD"} <= codes(r))
        self.assertEqual(a.fingerprint(), before)

    def test_unknown_parent_and_self_cycle_block(self):
        c = case()
        for parent, code in (("missing", "UNKNOWN_PARENT_SCENE"), ("scene1", "SCENE_PARENT_CYCLE")):
            r = coherence_qa(c.snapshot, architecture(c, (("scene1", (parent,)),)), beats(c))
            self.assertIn(code, codes(r))

    def test_realized_order_wins_over_sorted_architecture_ids(self):
        c = case(("We begin with the prerequisite.", "Now apply the idea."), scene_ids=("z_first", "a_second"))
        a = architecture(c, (("a_second", ("z_first",)),))
        a = replace(a, scenes=tuple(sorted(a.scenes, key=lambda s: s.scene_id)))
        r = coherence_qa(c.snapshot, a, beats(c))
        self.assertNotIn("PARENT_NOT_BEFORE_CHILD", codes(r))

    def test_missing_and_unplanned_scenes_block(self):
        c = case(); a = architecture(c)
        a = replace(a, scenes=(replace(a.scenes[0], scene_id="other"),))
        self.assertTrue({"SCENE_NOT_NARRATED", "SCENE_NOT_PLANNED"} <= codes(coherence_qa(c.snapshot, a, beats(c))))

    def test_lesson_objective_and_evidence_mismatch_block(self):
        c = case(); a = architecture(c)
        a = replace(a, lesson_id="other", objective_ids=("o1", "missing"), scenes=(replace(a.scenes[0], evidence_ids=("different",)),))
        self.assertTrue({"LESSON_MISMATCH", "LESSON_OBJECTIVE_UNCOVERED", "SCENE_LINEAGE_MISMATCH"} <= codes(coherence_qa(c.snapshot, a, beats(c))))

    def test_concepts_must_precede_use_unless_source_initial(self):
        c = case(); b = (replace(beats(c)[0], required_concepts=("base",)),)
        self.assertIn("CONCEPT_BEFORE_FOUNDATION", codes(coherence_qa(c.snapshot, architecture(c), b)))
        self.assertNotIn("CONCEPT_BEFORE_FOUNDATION", codes(coherence_qa(c.snapshot, architecture(c), b, initial_concepts=("base",))))

    def test_intro_then_reference_and_answer_resolve(self):
        c = case(("Why does the mechanism work?", "The mechanism uses a known foundation."))
        b = beats(c); b = (replace(b[0], introduced_concepts=("base",), opens_questions=("q1",)),
            replace(b[1], required_concepts=("base",), references=("u1",), answers_questions=("q1",)))
        self.assertEqual(coherence_qa(c.snapshot, architecture(c), b).status, "CHECKS_PASSED")

    def test_forward_unknown_reference_and_unanswered_question(self):
        c = case(); b = (replace(beats(c)[0], references=("u1", "missing"), opens_questions=("q",)),)
        self.assertTrue({"FORWARD_OR_UNKNOWN_REFERENCE", "UNRESOLVED_QUESTION"} <= codes(coherence_qa(c.snapshot, architecture(c), b)))

    def test_unknown_answer_duplicate_question_and_missing_beat(self):
        c = case(("First sentence has a question.", "Second sentence continues the question."))
        b = beats(c); b = (replace(b[0], opens_questions=("q",), answers_questions=("other",)), replace(b[1], opens_questions=("q",)))
        self.assertTrue({"ANSWER_WITHOUT_QUESTION", "QUESTION_ID_REUSED"} <= codes(coherence_qa(c.snapshot, architecture(c), b)))
        self.assertIn("DISCOURSE_ANNOTATION_MISSING", codes(coherence_qa(c.snapshot, architecture(c), b[:1])))

    def test_narrated_transition_binds_next_scene_and_actual_cue(self):
        c = case(("Here is the foundation.", "Now apply the idea."), scene_ids=("s1", "s2"))
        t = NarratedTransition(Transition("s1", "s2", "APPLICATION", c.snapshot.utterances[1].text), bind_span(c.snapshot, "u2"))
        r = coherence_qa(c.snapshot, architecture(c), beats(c), (t,))
        self.assertEqual(r.status, "CHECKS_PASSED")
        bad = replace(t, transition=replace(t.transition, cue="An unrealized cue.", relation="UNKNOWN"))
        self.assertTrue({"TRANSITION_CUE_NOT_REALIZED", "TRANSITION_RELATION_UNRESOLVED"} <= codes(coherence_qa(c.snapshot, architecture(c), beats(c), (bad,))))

    def test_stale_beat_and_duplicate_transition_rejected(self):
        c = case(); b = (replace(beats(c)[0], utterance_fingerprint="sha256:"+"0"*64),)
        with self.assertRaises(ValueError): coherence_qa(c.snapshot, architecture(c), b)
        t = NarratedTransition(Transition("scene1", "x", "APPLICATION", c.snapshot.utterances[0].text), bind_span(c.snapshot, "u1"))
        with self.assertRaises(ValueError): coherence_qa(c.snapshot, architecture(c), beats(c), (t, t))

    def test_architecture_review_propagates(self):
        c = case(); a = replace(architecture(c), requires_review=True)
        self.assertIn("ARCHITECTURE_REVIEW", codes(coherence_qa(c.snapshot, a, beats(c))))

    def test_report_replay_binds_annotations(self):
        c = case(); a = architecture(c); b = beats(c); r = coherence_qa(c.snapshot, a, b)
        self.assertEqual(validate_coherence_report(r, c.snapshot, a, b), r)
        with self.assertRaises(ValueError): validate_coherence_report(r, c.snapshot, a, ())
