from __future__ import annotations
from .contracts import StrategyKind, CognitiveOperation, KnowledgeForm, ScoreComponent
from .common import build_assessment, confidence_from_evidence, evidence_ids, fraction, runtime_blockers

def assess(bundle):
    bundle.validate();signals=bundle.equations;targets=[o for o in bundle.objectives if CognitiveOperation.SOLVE in o.cognitive_operations or KnowledgeForm.SYMBOLIC in o.knowledge_forms]
    target_ids={o.objective_id for o in targets};covered=target_ids & {s.objective_id for s in signals};vars_count=sum(len(s.variable_ids) for s in signals);ops_count=sum(len(s.operation_ids) for s in signals)
    blockers=[]
    if not targets:blockers.append('no_symbolic_or_solving_objective')
    if not signals:blockers.append('no_structured_equations')
    if targets and covered!=target_ids:blockers.append('incomplete_target_objective_coverage')
    required=('semantic_visuals','stateful_interaction','symbolic_math_runtime','accessibility_keyboard');blockers+=runtime_blockers(bundle.runtime,required)
    comps=(ScoreComponent('objective_fit',fraction(len(covered),len(target_ids)),4,'Coverage of symbolic/solve objectives'),ScoreComponent('symbolic_structure',fraction(vars_count+ops_count,max(1,3*len(signals))),3,'Equations expose structured variables and operations'),ScoreComponent('invariant_preservation',1.0 if signals and all(s.equivalence_invariant for s in signals) else 0.0,4,'Every equation declares balance/equivalence invariant'),ScoreComponent('manipulation_potential',fraction(ops_count,max(1,len(signals))),1,'Operations support learner transformation steps'))
    return build_assessment(strategy=StrategyKind.EQUATION,eligible=not blockers,components=comps,coverage=tuple(covered),blockers=tuple(blockers),strengths=('symbolic_manipulation','equivalence_reasoning','stepwise_feedback') if signals else (),runtime_required=required,design_requirements=('render_equation_as_semantic_objects_not_flat_text','animate_balance_preserving_operations','never_use_eval_or_string_execution','explain_why_each_operation_preserves_equivalence'),evidence_refs=evidence_ids([s.provenance for s in signals]+[o.provenance for o in targets]),confidence=confidence_from_evidence(len(signals),fraction(len(covered),len(target_ids)),0.52))
