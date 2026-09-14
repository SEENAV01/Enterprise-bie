"""Production composition boundary for the hardened BIE Director.

The assembly accepts only canonical RE/PED artifact references and configured
providers.  Scene plans, narration, claims and QA are always produced inside
the registered DIR executor.  Outputs remain review-only planning artifacts;
this boundary cannot assert render, gameplay, teaching quality or acceptance.
"""
from dataclasses import dataclass

from bie.bie_core.artifact_contracts import ArtifactRef
from bie.infrastructure.idempotency_store import SQLiteIdempotencyStore
from bie.infrastructure.orchestrator import ExecutionContext
from .annotated_directing import AnnotationRuntime
from .contract_validation import ids, nonblank
from .director_artifacts import DirectorArtifactIO
from .director_consumers import DirectorConsumers
from .director_durable_recovery import DirectorRecoveryCoordinator, SQLiteArtifactCatalog
from .director_executor import DirectorStageExecutor, register_director_stage
from .director_inputs import load_director_inputs
from .hierarchical_annotation_review import HierarchicalAnnotationReviewPolicy
from .hierarchical_annotations import HierarchicalAnnotationPolicy


@dataclass(frozen=True)
class ProductionSceneCorrection:
    scene_id: str
    reasons: tuple[str, ...]

    def validate(self):
        nonblank(self.scene_id, 'scene correction identity')
        ids(self.reasons, 'scene correction reasons')


@dataclass(frozen=True)
class DirectorProductionRequest:
    run_id: str
    idempotency_key: str
    attempt: int
    lesson_id: str
    title: str
    language: str
    reasoning_ref: ArtifactRef
    pedagogy_ref: ArtifactRef
    previous_idempotency_key: str | None = None
    scene_corrections: tuple[ProductionSceneCorrection, ...] = ()

    def validate(self):
        for value in (self.run_id, self.idempotency_key, self.lesson_id, self.title, self.language):
            nonblank(value, 'production request field')
        if type(self.attempt) is not int or not 1 <= self.attempt <= 3:
            raise ValueError('bounded production attempt required')
        if not isinstance(self.reasoning_ref, ArtifactRef) or not isinstance(self.pedagogy_ref, ArtifactRef):
            raise ValueError('typed canonical RE/PED references required')
        self.reasoning_ref.validate(); self.pedagogy_ref.validate()
        if self.reasoning_ref.artifact_type != 'reasoning.decision_set' or self.pedagogy_ref.artifact_type != 'pedagogy.plan':
            raise ValueError('exact canonical RE/PED artifact types required')
        if self.attempt == 1 and (self.previous_idempotency_key is not None or self.scene_corrections):
            raise ValueError('first attempt cannot request repair')
        if self.attempt > 1 and self.previous_idempotency_key is None:
            raise ValueError('repair attempt needs the exact previous idempotency key')
        if self.previous_idempotency_key is not None:
            nonblank(self.previous_idempotency_key, 'previous idempotency key')
            if self.previous_idempotency_key == self.idempotency_key:
                raise ValueError('repair requires a new idempotency key')
        for correction in self.scene_corrections:
            if not isinstance(correction, ProductionSceneCorrection):
                raise ValueError('typed production scene correction required')
            correction.validate()
        ids(tuple(c.scene_id for c in self.scene_corrections), 'corrected scene ids', required=False)


class DirectorProductionAssembly:
    """One durable, registered, hierarchical DIR composition root."""

    def __init__(self, io, idempotency, recovery, generator, generator_identity,
                 critic, critic_identity, annotations, *, policy=None, semantic_policy=None):
        if not isinstance(io, DirectorArtifactIO) or not isinstance(io.catalog, SQLiteArtifactCatalog):
            raise ValueError('production DIR requires a durable SQLite artifact catalog')
        if not isinstance(idempotency, SQLiteIdempotencyStore) or not isinstance(recovery, DirectorRecoveryCoordinator):
            raise ValueError('production DIR requires durable idempotency and fenced recovery')
        if not isinstance(annotations, AnnotationRuntime):
            raise ValueError('production DIR requires the annotation/review runtime')
        if (not isinstance(annotations.policy, HierarchicalAnnotationPolicy)
                or not isinstance(annotations.review_policy, HierarchicalAnnotationReviewPolicy)):
            raise ValueError('production DIR requires hierarchical annotation and review policies')
        if io.catalog.verify_durable_index():
            raise ValueError('durable artifact index integrity failed')
        kwargs = {'annotations': annotations, 'recovery': recovery}
        if policy is not None: kwargs['policy'] = policy
        if semantic_policy is not None: kwargs['semantic_policy'] = semantic_policy
        self.io, self.idempotency, self.recovery = io, idempotency, recovery
        self.executor = DirectorStageExecutor(io, idempotency, generator, generator_identity,
            critic, critic_identity, **kwargs)

    def descriptor(self):
        return {
            'schema_version': 'bie.dir.production_assembly/1.0.0',
            'artifact_catalog': 'SQLITE_INDEX_PLUS_CONTENT_ADDRESSED_STORAGE',
            'recovery': self.recovery.descriptor(),
            'annotation_runtime': self.executor.annotations.descriptor(),
            'review_boundary': 'IMPLEMENTATION_READY_REVIEW_REQUIRED_NOT_ACCEPTED',
        }

    def context(self, request):
        if not isinstance(request, DirectorProductionRequest):
            raise ValueError('typed DirectorProductionRequest required')
        request.validate()
        # This loads complete ancestry and source bytes before a provider call.
        load_director_inputs(self.io, request.reasoning_ref, request.pedagogy_ref,
            run_id=request.run_id, lesson_id=request.lesson_id, title=request.title, language=request.language)
        configuration = {'director': {
            'lesson_id': request.lesson_id, 'title': request.title, 'language': request.language}}
        if request.previous_idempotency_key is not None:
            repair = {'previous_idempotency_key': request.previous_idempotency_key}
            if request.scene_corrections:
                repair['scene_corrections'] = [
                    {'scene_id': item.scene_id, 'reasons': list(item.reasons)}
                    for item in request.scene_corrections]
            configuration['director_repair'] = repair
        return ExecutionContext(request.run_id, 'DIRECTOR', request.attempt, request.idempotency_key,
            [request.pedagogy_ref.artifact_id, request.reasoning_ref.artifact_id], configuration)

    def execute(self, request):
        return self.executor(self.context(request))

    def register(self, definitions, executors):
        return register_director_stage(definitions, executors, self.executor)

    def invalidate_superseded(self, run_id, superseded_refs, reason):
        """Explicit upstream revision hook; descendants become unreadable."""
        return self.executor.revisions.invalidate_inputs(self.io, run_id, tuple(superseded_refs), reason)

    def consumers(self):
        return DirectorConsumers(self.io, self.executor.revisions)
