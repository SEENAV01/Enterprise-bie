from __future__ import annotations
from .contracts import StrategyKind, CognitiveOperation, ScoreComponent
from .common import build_assessment, confidence_from_evidence, evidence_ids, fraction, runtime_blockers

def assess(bundle):
    bundle.validate();signals=bundle.predictions;targets=[o for o in bundle.objectives if CognitiveOperation.PREDICT in o.cognitive_operations]
    target_ids={o.objective_id for o in targets};covered=target_ids & {s.objective_id for s in signals};metrics=len({s.comparison_metric for s in signals})
    blockers=[]
    if not targets:blockers.append('no_prediction_objective')
    if not signals:blockers.append('no_prediction_targets')
    if targets and covered!=target_ids:blockers.append('incomplete_target_objective_coverage')
    required=('semantic_visuals','stateful_interaction','semantic_motion','audio_feedback');blockers+=runtime_blockers(bundle.runtime,required)
    comps=(ScoreComponent('objective_fit',fraction(len(covered),len(target_ids)),4,'Coverage of explicit prediction objectives'),ScoreComponent('precommit_integrity',1.0 if signals and all(s.commitment_before_observation for s in signals) else 0.0,3,'Predictions are committed before observations'),ScoreComponent('comparison_quality',fraction(metrics,max(1,len(signals))),2,'Explicit comparison metric per prediction target'),ScoreComponent('observable_outcome',fraction(len({s.observable_id for s in signals}),max(1,len(signals))),2,'Outcomes are observable and independently identified'))
    return build_assessment(strategy=StrategyKind.PREDICTION,eligible=not blockers,components=comps,coverage=tuple(covered),blockers=tuple(blockers),strengths=('commit_then_reveal','prediction_error_feedback','observable_outcomes') if signals else (),runtime_required=required,design_requirements=('capture_prediction_before_reveal','animate_observation_after_commit','compare_prediction_vs_outcome_visually','feedback_explains_model_not_just_correctness'),evidence_refs=evidence_ids([s.provenance for s in signals]+[o.provenance for o in targets]),confidence=confidence_from_evidence(len(signals),fraction(len(covered),len(target_ids)),0.5))
