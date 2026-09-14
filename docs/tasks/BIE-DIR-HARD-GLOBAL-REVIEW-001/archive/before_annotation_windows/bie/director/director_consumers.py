"""BIE-DIR-HARD-CONSUMERS-001: current, typed, review-only DIR consumers.

These entry points run the original timing, visual/animation sync and game
handoff functions on verified persisted director output. They produce planning
candidates, never visual plans, rendered media, a playable game or acceptance.
All descendants must be read through read_current; raw CAS reads are audit reads.
"""
from dataclasses import asdict
from .director_artifacts import DirectorArtifactIO, fingerprint, reference, canonical
from .director_revisions import DirectorRevisionStore
from .recovery_codec import decode, grounded_record
from .director_benchmark import DirectorExecution
from .director_inputs import load_director_inputs
from .narration_annotations import verify_base
from .qa_contract import QAReport, validate_snapshot, validate_claims
from .semantic_execution import SemanticEvaluation
from .pacing_qa import validate_timing
from .sync_contract import build_sync_context
from .narration_visual_sync import sync_visual_intents, VisualIntent
from .narration_animation_sync import sync_animation_intents
from .game_handoff import validate_game_handoff


CANDIDATES = {'director.timing_candidate', 'director.visual_sync_candidate',
              'director.animation_sync_candidate', 'director.game_handoff_candidate'}


class DirectorConsumers:
    def __init__(self, io, revisions):
        if not isinstance(io, DirectorArtifactIO) or not isinstance(revisions, DirectorRevisionStore):
            raise ValueError('canonical artifact IO and durable DIR revisions required')
        self.io, self.revisions = io, revisions

    def _director(self, ref):
        output = self.io.load(ref)
        self.revisions.assert_current(output)
        graph = self.io.load_graph((output.to_ref(),))
        for artifact in graph.values():
            if artifact.artifact_type == 'source.document':
                self.io.source_bytes(artifact.to_ref())
        p = output.payload
        evidence = self.io.load(reference(p['execution_evidence_ref']))
        if evidence.to_ref() not in output.parent_refs or evidence.artifact_type != 'evidence.director_execution':
            raise ValueError('missing actual director execution parent')
        raw = evidence.payload['result']
        if (fingerprint(raw) != p['result_fingerprint'] or p['result_fingerprint'] != evidence.payload['result_fingerprint']
                or p['execution'] != raw['execution']):
            raise ValueError('director candidate differs from retained execution')
        base_raw = raw.get('base_result', raw)
        base = grounded_record(base_raw)
        if p['plan'] != base_raw['plan'] or p['assessment_bindings'] != base_raw['generated_assessment_bindings']:
            raise ValueError('director plan/assessment binding mismatch')
        refs = {r.artifact_type: r for r in output.parent_refs}
        inputs = load_director_inputs(self.io, refs['reasoning.decision_set'], refs['pedagogy.plan'],
            lesson_id=p['lesson_id'], title=base.execution.architecture.title,
            language=base.execution.snapshot.language, run_id=output.run_id)
        verify_base(self.io, inputs, base)
        reports = decode(tuple[QAReport, ...], raw['qa_reports'])
        semantic = decode(SemanticEvaluation, raw['semantic_evaluation'])
        if 'BLOCKED' in (base.semantic_evaluation.status, semantic.status, *(r.status for r in reports)):
            raise ValueError('blocked director cannot feed consumers')
        for artifact in (output, evidence):
            if (artifact.metadata.get('status') not in ('REVIEW_REQUIRED', 'CHECKS_PASSED')
                    or artifact.metadata.get('requires_review') is not True
                    or artifact.metadata.get('release_ready') is not False
                    or artifact.metadata.get('accepted') is not False):
                raise ValueError('review boundary changed')
        execution = decode(DirectorExecution, raw['execution'])
        validate_snapshot(execution.snapshot); validate_claims(execution.snapshot, execution.claims)
        validate_timing(execution.snapshot, execution.speech, execution.pauses, execution.emphasis, execution.timeline)
        validate_game_handoff(execution.game_handoff)
        return output, execution

    def _persist(self, director, kind, result, parameters, extra_parents=()):
        # The final currentness check and write share a short SQLite lock. A
        # newer repair cannot race this write into appearing current.
        with self.revisions.guard(director):
            return self.io.derive(kind, director.run_id, (director.to_ref(),) + tuple(extra_parents),
                {'schema_version': 'bie.dir.consumer_candidate/1.0.0', 'consumer_kind': kind,
                 'director_ref': asdict(director.to_ref()), 'result': asdict(result),
                 'result_fingerprint': fingerprint(asdict(result)), 'parameters': parameters,
                 'review_boundary': 'PLANNING_PREVIEW_ONLY'}, stage_id='DIRECTOR',
                metadata={'requires_review': True, 'release_ready': False, 'accepted': False,
                          'status': 'BLOCKED' if getattr(result, 'status', None) == 'BLOCKED' else 'REVIEW_REQUIRED'})

    def timing(self, director_ref):
        output, execution = self._director(director_ref)
        context = build_sync_context(execution.speech, execution.pauses, execution.emphasis, execution.timeline)
        return self._persist(output, 'director.timing_candidate', context, {})

    def visual(self, director_ref, intents):
        output, execution = self._director(director_ref)
        context = build_sync_context(execution.speech, execution.pauses, execution.emphasis, execution.timeline)
        result = sync_visual_intents(context, intents)
        return self._persist(output, 'director.visual_sync_candidate', result, {'intents': [asdict(i) for i in intents]})

    def animation(self, director_ref, visual_ref, intents):
        output, execution = self._director(director_ref)
        visual = self.read_current(visual_ref)
        if visual.artifact_type != 'director.visual_sync_candidate' or visual.payload['director_ref'] != asdict(output.to_ref()):
            raise ValueError('visual sync belongs to another director revision')
        context = build_sync_context(execution.speech, execution.pauses, execution.emphasis, execution.timeline)
        # Recompute the original visual sync from its typed inputs, not a caller
        # supplied PASS or a guessed SyncPlan with untyped input objects.
        visual_inputs = decode(tuple[VisualIntent, ...], visual.payload['parameters']['intents'])
        visuals = sync_visual_intents(context, visual_inputs)
        if canonical(asdict(visuals)) != canonical(visual.payload['result']):
            raise ValueError('visual sync result differs from its original producer')
        result = sync_animation_intents(context, visuals, intents)
        return self._persist(output, 'director.animation_sync_candidate', result,
                             {'intents': [asdict(i) for i in intents]}, (visual.to_ref(),))

    def game_handoff(self, director_ref):
        output, execution = self._director(director_ref)
        return self._persist(output, 'director.game_handoff_candidate', validate_game_handoff(execution.game_handoff), {})

    def read_current(self, ref, *, purpose='PLANNING_PREVIEW'):
        if purpose != 'PLANNING_PREVIEW':
            raise ValueError('DIR candidates cannot authorize release, rendering or product acceptance')
        artifact = self.io.load(ref)
        if artifact.artifact_type not in CANDIDATES:
            raise ValueError('typed DIR consumer candidate required')
        graph = self.io.load_graph((artifact.to_ref(),))
        director = self.io.load(reference(artifact.payload['director_ref']))
        # Repair evidence may retain old director ancestors for audit. Only
        # active consumer dependency edges, not historical evidence, confer
        # currentness. Every chained candidate must point to this exact output.
        for item in graph.values():
            if item.artifact_type in CANDIDATES:
                if item.payload['director_ref'] != asdict(director.to_ref()):
                    raise ValueError('mixed or stale consumer revision')
                if (director.to_ref() not in item.parent_refs or item.payload.get('consumer_kind') != item.artifact_type
                        or item.payload.get('schema_version') != 'bie.dir.consumer_candidate/1.0.0'):
                    raise ValueError('consumer dependency/type binding mismatch')
                if (fingerprint(item.payload['result']) != item.payload['result_fingerprint']
                        or item.payload['review_boundary'] != 'PLANNING_PREVIEW_ONLY'
                        or item.metadata.get('requires_review') is not True or item.metadata.get('accepted') is not False
                        or item.metadata.get('release_ready') is not False or item.metadata.get('status') != 'REVIEW_REQUIRED'):
                    raise ValueError('blocked or weakened consumer candidate')
        self._director(director.to_ref())
        with self.revisions.guard(director):
            return artifact
