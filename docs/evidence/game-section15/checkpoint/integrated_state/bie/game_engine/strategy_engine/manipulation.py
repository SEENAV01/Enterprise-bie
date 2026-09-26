from __future__ import annotations
from .contracts import StrategyKind, CognitiveOperation, KnowledgeForm, ScoreComponent
from .common import build_assessment, confidence_from_evidence, evidence_ids, fraction, runtime_blockers

def assess(bundle):
    bundle.validate();signals=bundle.manipulations;targets=[o for o in bundle.objectives if CognitiveOperation.MANIPULATE in o.cognitive_operations or KnowledgeForm.PROCEDURE in o.knowledge_forms]
    target_ids={o.objective_id for o in targets};covered=target_ids & {s.objective_id for s in signals};effects=sum(len(s.observable_effect_ids) for s in signals)
    blockers=[]
    if not targets:blockers.append('no_manipulation_or_procedural_objective')
    if not signals:blockers.append('no_bounded_manipulable_variables')
    if targets and covered!=target_ids:blockers.append('incomplete_target_objective_coverage')
    required=('semantic_visuals','stateful_interaction','semantic_motion','drag_drop','parameter_controls','accessibility_keyboard');blockers+=runtime_blockers(bundle.runtime,required)
    comps=(ScoreComponent('objective_fit',fraction(len(covered),len(target_ids)),4,'Coverage of manipulation/procedure objectives'),ScoreComponent('state_action_density',fraction(len(signals),max(1,len(targets))),2,'Grounded controllable state per target objective'),ScoreComponent('observable_causality',fraction(effects,max(1,len(signals))),3,'Learner actions produce observable semantic effects'),ScoreComponent('safety_resetability',1.0 if signals and all(s.reversible and s.bounded for s in signals) else 0.0,2,'All manipulations are bounded and reversible'))
    return build_assessment(strategy=StrategyKind.MANIPULATION,eligible=not blockers,components=comps,coverage=tuple(covered),blockers=tuple(blockers),strengths=('direct_state_control','visible_cause_effect','resettable_experiment') if signals else (),runtime_required=required,design_requirements=('learner_controls_semantic_objects_not_ui_chrome','state_change_must_be_visually_observable','motion_explains_cause_effect','keyboard_equivalent_for_spatial_actions','no_drag_for_decoration_only'),evidence_refs=evidence_ids([s.provenance for s in signals]+[o.provenance for o in targets]),confidence=confidence_from_evidence(len(signals),fraction(len(covered),len(target_ids)),0.5))
