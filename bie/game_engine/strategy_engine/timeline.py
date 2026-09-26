from __future__ import annotations
from collections import Counter
from .contracts import StrategyKind, CognitiveOperation, KnowledgeForm, ScoreComponent
from .common import build_assessment, confidence_from_evidence, evidence_ids, fraction, runtime_blockers

def assess(bundle):
    bundle.validate();signals=bundle.temporal_events;targets=[o for o in bundle.objectives if CognitiveOperation.ORDER in o.cognitive_operations or KnowledgeForm.TEMPORAL in o.knowledge_forms]
    target_ids={o.objective_id for o in targets};covered=target_ids & {s.objective_id for s in signals};counts=Counter(s.objective_id for s in signals);distinct_orders=len({s.order_key for s in signals})
    blockers=[]
    if not targets:blockers.append('no_temporal_or_ordering_objective')
    if len(signals)<2:blockers.append('insufficient_temporal_events')
    if targets and covered!=target_ids:blockers.append('incomplete_target_objective_coverage')
    if any(counts[x]<2 for x in target_ids):blockers.append('objective_has_fewer_than_two_events')
    required=('semantic_visuals','stateful_interaction','semantic_motion','timeline_runtime','accessibility_keyboard');blockers+=runtime_blockers(bundle.runtime,required)
    comps=(ScoreComponent('objective_fit',fraction(len(covered),len(target_ids)),4,'Coverage of temporal/order objectives'),ScoreComponent('sequence_depth',fraction(len(signals),max(2,3*len(targets))),2,'Enough events to support reconstruction rather than trivial ordering'),ScoreComponent('temporal_resolution',fraction(distinct_orders,max(1,len(signals))),2,'Distinct temporal anchors support meaningful ordering'),ScoreComponent('grounded_anchors',1.0 if signals and all(s.anchor_ref for s in signals) else 0.0,2,'Every event has an evidence-backed anchor'))
    return build_assessment(strategy=StrategyKind.TIMELINE,eligible=not blockers,components=comps,coverage=tuple(covered),blockers=tuple(blockers),strengths=('temporal_reconstruction','stable_ordering','evidence_backed_events') if signals else (),runtime_required=required,design_requirements=('represent_time_spatially_and_semantically','animate_reordering_as_state_change','support_keyboard_reordering','show_causal_links_separately_from_chronology'),evidence_refs=evidence_ids([s.provenance for s in signals]+[o.provenance for o in targets]),confidence=confidence_from_evidence(len(signals),fraction(len(covered),len(target_ids)),0.5))
