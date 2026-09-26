from __future__ import annotations
from .contracts import StrategyKind, CognitiveOperation, KnowledgeForm, ScoreComponent
from .common import build_assessment, confidence_from_evidence, evidence_ids, fraction, runtime_blockers

def assess(bundle):
    bundle.validate();signals=bundle.simulations;targets=[o for o in bundle.objectives if CognitiveOperation.MODEL in o.cognitive_operations or KnowledgeForm.SYSTEM in o.knowledge_forms]
    target_ids={o.objective_id for o in targets};covered=target_ids & {s.objective_id for s in signals};param_count=sum(len(s.parameter_ids) for s in signals);output_count=sum(len(s.output_ids) for s in signals)
    blockers=[]
    if not targets:blockers.append('no_model_or_system_objective')
    if not signals:blockers.append('no_grounded_simulation_model')
    if targets and covered!=target_ids:blockers.append('incomplete_target_objective_coverage')
    if any(not s.model_scope.strip() for s in signals):blockers.append('simulation_scope_not_declared')
    required=('semantic_visuals','stateful_interaction','semantic_motion','simulation_runtime','parameter_controls','purposeful_camera');blockers+=runtime_blockers(bundle.runtime,required)
    comps=(ScoreComponent('objective_fit',fraction(len(covered),len(target_ids)),4,'Coverage of model/system objectives'),ScoreComponent('parameter_richness',fraction(param_count,max(1,2*len(signals))),2,'Model exposes meaningful learner-controllable parameters'),ScoreComponent('observable_outputs',fraction(output_count,max(1,len(signals))),3,'Model exposes measurable outputs'),ScoreComponent('scope_truthfulness',1.0 if signals and all(s.model_scope for s in signals) else 0.0,2,'Each model declares its evidence-bounded scope'))
    return build_assessment(strategy=StrategyKind.SIMULATION,eligible=not blockers,components=comps,coverage=tuple(covered),blockers=tuple(blockers),strengths=('parameter_experimentation','observable_model_response','declared_model_scope') if signals else (),runtime_required=required,design_requirements=('visualize_model_state_continuously','show_parameter_to_output_causality','label_model_limits_and_assumptions','camera_tracks_semantic_change_not_random_motion','never_present_simulation_as_unqualified_ground_truth'),evidence_refs=evidence_ids([s.provenance for s in signals]+[o.provenance for o in targets]),confidence=confidence_from_evidence(len(signals),fraction(len(covered),len(target_ids)),0.52))
