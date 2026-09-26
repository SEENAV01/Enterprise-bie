from __future__ import annotations
from .contracts import StrategyKind, CognitiveOperation, ScoreComponent
from .common import build_assessment, confidence_from_evidence, evidence_ids, fraction, runtime_blockers

def assess(bundle):
    bundle.validate();signals=bundle.diagnostics;targets=[o for o in bundle.objectives if CognitiveOperation.DIAGNOSE in o.cognitive_operations or o.misconception_ids]
    target_ids={o.objective_id for o in targets};covered=target_ids & {s.objective_id for s in signals};known={m for o in targets for m in o.misconception_ids};case_mis={s.misconception_id for s in signals}
    blockers=[]
    if not targets:blockers.append('no_diagnostic_or_misconception_objective')
    if not signals:blockers.append('no_grounded_diagnostic_cases')
    if targets and covered!=target_ids:blockers.append('incomplete_target_objective_coverage')
    if known and not known<=case_mis:blockers.append('misconception_case_coverage_incomplete')
    required=('semantic_visuals','stateful_interaction','accessibility_keyboard','audio_feedback');blockers+=runtime_blockers(bundle.runtime,required)
    comps=(ScoreComponent('objective_fit',fraction(len(covered),len(target_ids)),4,'Coverage of diagnostic objectives'),ScoreComponent('misconception_coverage',fraction(len(known & case_mis),len(known)),4,'Known misconceptions have grounded diagnostic cases'),ScoreComponent('explanation_availability',fraction(len({s.correct_explanation_ref for s in signals}),max(1,len(signals))),2,'Each case binds to a corrective explanation'),ScoreComponent('case_diversity',fraction(len({s.incorrect_state_ref for s in signals}),max(1,len(signals))),1,'Distinct incorrect states avoid repetitive traps'))
    return build_assessment(strategy=StrategyKind.DIAGNOSTIC,eligible=not blockers,components=comps,coverage=tuple(covered),blockers=tuple(blockers),strengths=('misconception_specific_feedback','error_localization','explanation_grounding') if signals else (),runtime_required=required,design_requirements=('show_learner_the_error_state_semantically','ask_for_diagnosis_before_correction','feedback_names_reasoning_error_not_person','never_use_gotcha_traps_without_explanation'),evidence_refs=evidence_ids([s.provenance for s in signals]+[o.provenance for o in targets]),confidence=confidence_from_evidence(len(signals),fraction(len(covered),len(target_ids)),0.55))
