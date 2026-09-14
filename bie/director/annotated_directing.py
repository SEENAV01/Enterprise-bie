"""BIE-DIR-HARD-ANNOTATION-QA-001: actual annotation/QA/timing composition.

Keeps the previous whole-utterance factual guard. Finer labels can never remove
its reported contradictions, or convert an unreviewed candidate into a release.
"""
from dataclasses import asdict, dataclass, replace
from .director_artifacts import fingerprint
from .director_model import DirectingFailure, model_identity
from .narration_annotations import AnnotationPolicy, produce_annotations, verify_production
from .annotation_review import (AnnotationReviewPolicy, review_annotations, annotation_review_qa,
                                approved_subjects)
from .semantic_execution import evaluate_script_semantics
from .script_coherence_qa import coherence_qa
from .age_level_qa import age_level_qa, AudiencePolicy
from .repetition_detection import repetition_qa
from .pacing_qa import pacing_qa
from .emphasis_timing import build_emphasis_timing
from .scene_duration_fit import fit_scene_durations
from .assessment_prompts import AssessmentPrompt


@dataclass(frozen=True)
class AnnotatedDirectorResult:
    base_result:object
    annotation_production:object
    annotation_review:object
    execution:object
    semantic_evaluation:object
    qa_reports:tuple
    applied_repetition_subjects:tuple[str,...]
    limitations:tuple[str,...]

    @property
    def plan(self):return self.base_result.plan
    @property
    def input_fingerprint(self):return self.base_result.input_fingerprint
    @property
    def generated_assessment_bindings(self):return self.base_result.generated_assessment_bindings
    @property
    def generation_attempts(self):
        return self.base_result.generation_attempts+self.annotation_production.attempts+self.annotation_review.attempts
    @property
    def status(self):
        statuses=[self.base_result.semantic_evaluation.status,self.semantic_evaluation.status]+[r.status for r in self.qa_reports]
        if 'BLOCKED' in statuses:return 'BLOCKED'
        if 'REVIEW_REQUIRED' in statuses:return 'REVIEW_REQUIRED'
        return 'CHECKS_PASSED'
    @property
    def accepted(self):return False
    def fingerprint(self):return fingerprint(asdict(self))


@dataclass(frozen=True)
class AnnotationRuntime:
    annotator:object
    annotator_identity:object
    reviewer:object
    reviewer_identity:object
    policy:AnnotationPolicy=AnnotationPolicy()
    review_policy:AnnotationReviewPolicy=AnnotationReviewPolicy()

    def validate(self):
        self.policy.validate();self.review_policy.validate()
        model_identity(self.annotator_identity);model_identity(self.reviewer_identity)
        if not callable(getattr(self.annotator,'invoke',None)) or not callable(getattr(self.reviewer,'invoke',None)):
            raise ValueError('configured annotation and review ModelProviders required')
        if (self.annotator_identity.provider,self.annotator_identity.model)==(self.reviewer_identity.provider,self.reviewer_identity.model):
            raise ValueError('annotation reviewer must have a separate configured model identity')

    def descriptor(self):
        self.validate()
        return {'schema_version':'bie.dir.annotation_runtime/1.0.0','annotator':asdict(self.annotator_identity),
            'reviewer':asdict(self.reviewer_identity),'annotation_policy':asdict(self.policy),'review_policy':asdict(self.review_policy)}

    def enrich(self,io,inputs,base,factual_provider,factual_identity,semantic_policy,*,reuse=None):
        self.validate()
        if base.status=='BLOCKED':raise DirectingFailure('ANNOTATION_REQUIRES_NONBLOCKED_BASE',base.generation_attempts,'DIR_QA')
        try:production=produce_annotations(io,inputs,base,self.annotator,self.annotator_identity,self.policy,reuse=reuse)
        except DirectingFailure as failure:
            raise DirectingFailure(failure.code,base.generation_attempts+failure.attempts,'DIR_ANNOTATIONS') from None
        annotations=verify_production(production,inputs,base)
        review=review_annotations(inputs,base,production,self.reviewer,self.reviewer_identity,self.review_policy)
        reviewed=annotation_review_qa(base.execution.snapshot,production,review)
        approved=approved_subjects(annotations,review)
        confidence={r.subject_id:r.confidence for r in annotations.rationales}
        def admitted(subject):return subject in approved and confidence.get(subject,1)>=self.policy.minimum_confidence
        # Repetition exceptions can suppress lexical warnings, so only an actual
        # complete policy-listed review can authorize their use in the old QA.
        repetitions=[];applied=[]
        for repetition in annotations.repetitions:
            key='repeat:'+fingerprint((asdict(repetition.first),asdict(repetition.repeated)))
            if admitted(key) and admitted('completeness:REPETITION'):
                repetitions.append(repetition);applied.append(key)
        audience_subjects=[r.subject_id for r in annotations.rationales if r.subject_id.startswith(('term:','advisory:'))]
        audience_reviewed=admitted('completeness:AUDIENCE') and all(admitted(s) for s in audience_subjects)
        # Emphasis is a provisional timing plan. Contrary/uncertain reviews remain
        # blockers/review; no audio waveform or narration is modified here.
        emphasis=build_emphasis_timing(base.execution.speech,annotations.emphasis,base.execution.emphasis.policy)
        timeline=fit_scene_durations(base.execution.speech,base.execution.pauses,emphasis,
            base.execution.timeline.targets,base.execution.timeline.policy)
        execution=replace(base.execution,claims=annotations.claims,emphasis=emphasis,timeline=timeline)
        semantic=evaluate_script_semantics(execution.snapshot,execution.claims,inputs.catalog,inputs.sources,
            factual_provider,factual_identity,semantic_policy)
        cells={item:cell for binding in inputs.bindings for cell in binding.assessments for item in cell.item_ids}
        assessments=tuple(AssessmentPrompt(cells[a.item_id].objective_id,cells[a.item_id].cognitive_level,a.question,
            ' '.join((a.expected_answer,)+a.success_criteria),a.evidence_ids) for n in base.narrated_scenes for a in n.assessments)
        qa=(coherence_qa(execution.snapshot,execution.architecture,annotations.discourse,annotations.transitions),
            repetition_qa(execution.snapshot,tuple(repetitions)),
            age_level_qa(execution.snapshot,self.policy.audience_target,annotations.terms,annotations.advisories,
                assessments,AudiencePolicy(annotation_review_completed=audience_reviewed)),
            pacing_qa(execution.snapshot,execution.speech,execution.pauses,execution.emphasis,execution.timeline,
                annotations.pacing,self.policy.pacing_policy),reviewed)
        return AnnotatedDirectorResult(base,production,review,execution,semantic,qa,tuple(applied),(
            'Whole-utterance factual results remain a guard; finer labels and repetition purposes cannot erase contradictions.',
            'Annotation and reviewer responses are model-reported interpretations; policy-listed does not mean authenticated truth or calibrated quality.',
            'Audience and term/advisory policies are optional curriculum inputs, never inferred learner ages, questionnaire answers or measured mastery.',
            'Emphasis changes estimated planning events only; actual speech text and assessment response-time requirements are unchanged.',
            'Source/voice edits require bounded correction or fresh generation, global review and downstream invalidation; actual audio/game execution remains downstream evidence.'))
