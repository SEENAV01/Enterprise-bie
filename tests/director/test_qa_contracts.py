"""Contract bridges, not end-to-end media or learning acceptance."""
import unittest
from dataclasses import replace
from bie.director.qa_contract import snapshot_script, bind_span
from bie.director.factual_script_qa import factual_qa, validate_factual_report
from bie.director.source_grounding_qa import source_grounding_qa, SourceBytes
from bie.director.script_coherence_qa import coherence_qa, DiscourseBeat
from bie.director.repetition_detection import repetition_qa
from bie.director.age_level_qa import age_level_qa
from bie.director.speech_timing import estimate_speech
from bie.director.pause_timing import build_pause_timing
from bie.director.emphasis_timing import build_emphasis_timing
from bie.director.sync_contract import build_sync_context, SyncIndex, IntentBinding
from bie.director.narration_visual_sync import sync_visual_intents, VisualIntent, validate_visual_sync
from bie.knowledge_intelligence.claim_evidence import bind as ki_bind
from bie.knowledge_intelligence.ki_unsupported_claims_qa import evaluate as ki_evaluate
from bie.qa.release_contracts import GateEvidence, ReleaseEvaluator, enterprise_default_policy
from qa_fixtures import case, codes
from test_qa_003 import architecture


def timing(snapshot, wpm=120):
    speech = estimate_speech(snapshot.utterances, wpm=wpm)
    return build_sync_context(speech, build_pause_timing(speech), build_emphasis_timing(speech))


def visual(snapshot, context):
    u = snapshot.utterances[0]; index = SyncIndex(context)
    a = index.anchor(u.utterance_id, 0, len(context.speech.utterances[0].words))
    b = IntentBinding("v", "diagram1", a, u.evidence_ids, u.objective_ids, ("concept1",), "Explain source concept")
    return sync_visual_intents(context, (VisualIntent(b, "diagram"),))


class QAContractTests(unittest.TestCase):
    def test_qa_and_visual_share_actual_realized_narration_spans(self):
        c = case(); ctx = timing(c.snapshot); v = visual(c.snapshot, ctx)
        span = c.claims[0].span; window = v.cues[0].window
        self.assertEqual((window.start_char, window.end_char), (span.start_char, span.end_char-1))
        # SYNC word span excludes punctuation; QA claim intentionally includes it.
        self.assertEqual(span.utterance_fingerprint, ctx.speech.utterances[0].utterance.fingerprint())
        self.assertFalse(v.accepted); self.assertFalse(factual_qa(c.snapshot, c.claims, c.catalog).accepted)

    def test_narration_edit_invalidates_previous_qa_and_sync(self):
        c = case(); ctx = timing(c.snapshot); v = visual(c.snapshot, ctx)
        r = factual_qa(c.snapshot, c.claims, c.catalog)
        changed = case(("A rectangle has four straight sides.",)); new_ctx = timing(changed.snapshot)
        with self.assertRaises(ValueError): validate_factual_report(r, changed.snapshot, changed.claims, changed.catalog)
        with self.assertRaises(ValueError): validate_visual_sync(new_ctx, v)

    def test_wpm_change_leaves_text_qa_valid_but_requires_sync_rebuild(self):
        c = case(); old = timing(c.snapshot); new = timing(c.snapshot, wpm=90)
        r = factual_qa(c.snapshot, c.claims, c.catalog); v = visual(c.snapshot, old)
        self.assertEqual(validate_factual_report(r, c.snapshot, c.claims, c.catalog), r)
        with self.assertRaises(ValueError): validate_visual_sync(new, v)
        self.assertGreater(visual(c.snapshot, new).cues[0].window.end_ms, v.cues[0].window.end_ms)

    def test_existing_ki_metadata_grounded_flag_is_not_semantic_or_byte_proof(self):
        c = case(); binding = ki_bind("c1", ("e1",), .99)
        self.assertTrue(binding["grounded"]); self.assertTrue(ki_evaluate((binding,))["passed"])
        self.assertEqual(factual_qa(c.snapshot, c.claims, c.catalog).status, "REVIEW_REQUIRED")
        self.assertIn("SOURCE_BYTES_MISSING", codes(source_grounding_qa(c.snapshot, c.claims, c.catalog)))

    def test_grounded_wrong_fact_does_not_pass_factual_qa(self):
        c = case(("The measured length is 15 cm.",), ("The measured length is 12 cm.",))
        artifacts = tuple(SourceBytes(s, b, "text/plain; charset=utf-8") for s, b in c.source_data)
        self.assertEqual(source_grounding_qa(c.snapshot, c.claims, c.catalog, artifacts).status, "CHECKS_PASSED")
        self.assertEqual(factual_qa(c.snapshot, c.claims, c.catalog).status, "BLOCKED")

    def test_partial_qa_evidence_cannot_satisfy_enterprise_release(self):
        c = case(); artifacts = tuple(SourceBytes(s, b, "text/plain; charset=utf-8") for s, b in c.source_data)
        r = source_grounding_qa(c.snapshot, c.claims, c.catalog, artifacts)
        evidence = [GateEvidence("controlled-source-qa", "source_grounding", "PASS", "controlled-fixture", "1",
            [r.snapshot_fingerprint], [r.fingerprint()], summary="Only synthetic UTF-8 source grounding checked")]
        decision = ReleaseEvaluator.evaluate(enterprise_default_policy(), evidence)
        self.assertEqual(decision.release_status, "BLOCKED")
        self.assertTrue({"director_quality", "semantic_correctness", "video_render", "game_runtime"} <= set(decision.blocking_gates))

    def test_upstream_script_review_survives_all_five_qa_gates(self):
        c = case(); d = replace(c.snapshot.drafts[0], requires_review=True)
        c.snapshot = snapshot_script(c.snapshot.script, (d,), ("u1",))
        claims = (replace(c.claims[0], span=bind_span(c.snapshot, "u1")),)
        b = (DiscourseBeat("u1", c.snapshot.utterances[0].fingerprint()),)
        artifacts = tuple(SourceBytes(s, data, "text/plain; charset=utf-8") for s, data in c.source_data)
        results = (factual_qa(c.snapshot, claims, c.catalog), source_grounding_qa(c.snapshot, claims, c.catalog, artifacts),
            coherence_qa(c.snapshot, architecture(c), b), repetition_qa(c.snapshot), age_level_qa(c.snapshot))
        self.assertEqual(len({r.task_id for r in results}), 5)
        for r in results:
            self.assertIn("UPSTREAM_REVIEW", codes(r)); self.assertFalse(r.accepted)

    def test_no_duration_cap_or_profile_needed_to_run_qa_and_timing(self):
        text = "Explain this grounded source concept carefully. " * 40
        c = case((text.strip(),)); ctx = timing(c.snapshot)
        before = c.snapshot.fingerprint(); r = age_level_qa(c.snapshot)
        self.assertIn("AUDIENCE_TARGET_UNSPECIFIED", codes(r))
        self.assertGreater(ctx.timeline.scenes[0].duration_ms, 60000)
        self.assertEqual(before, c.snapshot.fingerprint())
