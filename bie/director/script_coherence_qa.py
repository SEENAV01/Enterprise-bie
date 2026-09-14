"""BIE-DIR-QA-003: structural discourse checks over actual narration order.

Concept/reference annotations are explicit upstream inputs. This is neither
automatic semantic understanding nor a replacement for pedagogical evaluation.
"""
from dataclasses import dataclass
from .qa_contract import (TextSpan, Finding, immutable, rows, validate_snapshot,
                          span_text, report, verify_report)
from .timing_contract import identifiers, nonblank
from .lesson_architecture_contract import LessonArchitecture, LessonSceneIntent
from .transition_strategy import Transition


@dataclass(frozen=True)
class DiscourseBeat:
    utterance_id: str
    utterance_fingerprint: str
    introduced_concepts: tuple[str, ...] = ()
    required_concepts: tuple[str, ...] = ()
    references: tuple[str, ...] = ()  # prior utterance IDs, not ambiguous pronouns
    opens_questions: tuple[str, ...] = ()
    answers_questions: tuple[str, ...] = ()


@dataclass(frozen=True)
class NarratedTransition:
    transition: Transition
    cue_span: TextSpan


def coherence_qa(snapshot, architecture, beats, transitions=(), initial_concepts=(),
                 policy_version="bie-dir-coherence/1.0.0"):
    index = validate_snapshot(snapshot)
    if not isinstance(architecture, LessonArchitecture):
        raise ValueError("expected original LessonArchitecture")
    immutable(architecture)
    rows(architecture.scenes, LessonSceneIntent, "lesson scenes", "scene_id")
    rows(beats, DiscourseBeat, "beats", "utterance_id")
    rows(transitions, NarratedTransition, "transitions")
    identifiers(initial_concepts, "source-derived initial concepts", allow_empty=True)
    for name in ("lesson_id", "title", "policy_version"):
        nonblank(getattr(architecture, name), name)
    identifiers(architecture.objective_ids, "lesson objectives")
    identifiers(architecture.source_ids, "lesson sources")
    if type(architecture.requires_review) is not bool:
        raise ValueError("invalid architecture review flag")
    findings = []
    def add(code, severity, subject, detail):
        findings.append(Finding(code, severity, subject, detail, "DIR_COHERENCE"))
    if architecture.lesson_id != snapshot.script.lesson_id:
        add("LESSON_MISMATCH", "BLOCKER", architecture.lesson_id, "Architecture and script belong to different lessons.")
    if architecture.requires_review:
        add("ARCHITECTURE_REVIEW", "REVIEW", architecture.lesson_id, "Original lesson review remains open.")
    scenes = {s.scene_id: s for s in architecture.scenes}
    order = tuple(dict.fromkeys(u.scene_id for u in snapshot.utterances))
    positions = {sid: i for i, sid in enumerate(order)}
    for sid in sorted(set(scenes) - set(order)):
        add("SCENE_NOT_NARRATED", "BLOCKER", sid, "Planned scene is absent from realized narration.")
    for sid in sorted(set(order) - set(scenes)):
        add("SCENE_NOT_PLANNED", "BLOCKER", sid, "Narration uses a scene outside the lesson architecture.")
    parents = {}
    for s in architecture.scenes:
        nonblank(s.purpose, "scene purpose")
        identifiers(s.evidence_ids, "scene evidence")
        identifiers(s.objective_ids, "scene objectives")
        identifiers(s.parent_scene_ids, "parent scenes", allow_empty=True)
        if type(s.requires_review) is not bool:
            raise ValueError("invalid scene review flag")
        if s.requires_review:
            add("SCENE_REVIEW", "REVIEW", s.scene_id, "Original scene review remains open.")
        parents[s.scene_id] = set(s.parent_scene_ids) & set(scenes)
        for parent in s.parent_scene_ids:
            if parent not in scenes:
                add("UNKNOWN_PARENT_SCENE", "BLOCKER", s.scene_id, "Unknown parent: " + parent)
            elif s.scene_id in positions and parent in positions and positions[parent] >= positions[s.scene_id]:
                add("PARENT_NOT_BEFORE_CHILD", "BLOCKER", s.scene_id, "Required scene must precede its child: " + parent)
        if not set(s.objective_ids) <= set(architecture.objective_ids):
            add("SCENE_OBJECTIVE_OUTSIDE_LESSON", "BLOCKER", s.scene_id, "Scene objectives are outside the lesson contract.")
    # Kahn elimination detects legacy parent cycles without recursion limits.
    remaining = dict(parents)
    while remaining:
        ready = {k for k, deps in remaining.items() if not deps}
        if not ready:
            add("SCENE_PARENT_CYCLE", "BLOCKER", architecture.lesson_id,
                "Parent graph is cyclic; affected scenes: " + ", ".join(sorted(remaining)))
            break
        remaining = {k: deps-ready for k, deps in remaining.items() if k not in ready}
    narrated_objectives = set()
    for u in snapshot.utterances:
        narrated_objectives.update(u.objective_ids)
        if u.scene_id in scenes:
            s = scenes[u.scene_id]
            if not set(u.objective_ids) <= set(s.objective_ids) or not set(u.evidence_ids) <= set(s.evidence_ids):
                add("SCENE_LINEAGE_MISMATCH", "BLOCKER", u.utterance_id, "Draft evidence/objectives are outside its planned scene.")
    for obj in sorted(set(architecture.objective_ids) - narrated_objectives):
        add("LESSON_OBJECTIVE_UNCOVERED", "BLOCKER", obj, "No realized segment names this objective; semantic coverage remains separate.")
    by_beat = {}
    for b in beats:
        if b.utterance_id not in index or b.utterance_fingerprint != index[b.utterance_id].fingerprint():
            raise ValueError("stale or unknown discourse beat")
        for name in ("introduced_concepts", "required_concepts", "references", "opens_questions", "answers_questions"):
            identifiers(getattr(b, name), name, allow_empty=True)
        by_beat[b.utterance_id] = b
    seen, known, open_questions, ever_opened = set(), set(initial_concepts), {}, set()
    for u in snapshot.utterances:
        b = by_beat.get(u.utterance_id)
        if b is None:
            add("DISCOURSE_ANNOTATION_MISSING", "REVIEW", u.utterance_id, "Concept/reference coherence has not been annotated.")
        else:
            for concept in sorted(set(b.required_concepts) - known):
                add("CONCEPT_BEFORE_FOUNDATION", "BLOCKER", u.utterance_id, "Required concept has not been introduced: " + concept)
            for ref in b.references:
                if ref not in seen:
                    add("FORWARD_OR_UNKNOWN_REFERENCE", "BLOCKER", u.utterance_id, "Antecedent must already have been narrated: " + ref)
            for q in b.opens_questions:
                if q in ever_opened:
                    add("QUESTION_ID_REUSED", "BLOCKER", u.utterance_id, "Question IDs must identify one opening: " + q)
                open_questions[q] = u.utterance_id
                ever_opened.add(q)
            for q in b.answers_questions:
                if q not in open_questions:
                    add("ANSWER_WITHOUT_QUESTION", "REVIEW", u.utterance_id, "No currently open question: " + q)
                else:
                    del open_questions[q]
            known.update(b.introduced_concepts)
        seen.add(u.utterance_id)
    for q, uid in sorted(open_questions.items()):
        add("UNRESOLVED_QUESTION", "REVIEW", uid, "Question needs resolution or explicit handoff: " + q)
    edges = set(zip(order, order[1:]))
    supplied = set()
    for t in transitions:
        if not isinstance(t.transition, Transition):
            raise ValueError("expected original Transition")
        for name in ("from_scene", "to_scene", "relation", "cue"):
            nonblank(getattr(t.transition, name), "transition " + name)
        edge = (t.transition.from_scene, t.transition.to_scene)
        if edge in supplied:
            raise ValueError("duplicate scene transition")
        supplied.add(edge)
        text = span_text(index, t.cue_span)
        if edge not in edges or index[t.cue_span.utterance_id].scene_id != edge[1]:
            add("TRANSITION_OUT_OF_ORDER", "BLOCKER", t.cue_span.utterance_id, "Transition must enter the next narrated scene.")
        if text != t.transition.cue:
            add("TRANSITION_CUE_NOT_REALIZED", "BLOCKER", t.cue_span.utterance_id, "Narrated span differs from declared transition cue.")
        if t.transition.relation not in ("CAUSE", "PREREQUISITE", "CONTRAST", "EVIDENCE", "APPLICATION"):
            add("TRANSITION_RELATION_UNRESOLVED", "REVIEW", t.cue_span.utterance_id, "Generic cue has no resolved discourse relation.")
    for a, b in sorted(edges - supplied):
        add("TRANSITION_UNANNOTATED", "REVIEW", b, "No revision-bound transition from " + a)
    return report("BIE-DIR-QA-003", snapshot, (architecture, beats, transitions, initial_concepts, policy_version),
        policy_version, findings, (("narrated_scenes", len(order)), ("annotated_utterances", len(beats)),
            ("unresolved_questions", len(open_questions))),
        "Structural lesson order, declared concept/reference/question and transition coherence",
        ("Annotations are upstream assertions; semantic explanation quality requires independent evaluation.",
         "Objective ID coverage is not demonstrated learner understanding.",
         "Legacy source defects are detected at this boundary, not rewritten by this QA module."))


def validate_coherence_report(actual, *args, **kwargs):
    return verify_report(actual, coherence_qa(*args, **kwargs))
