from __future__ import annotations
from collections import defaultdict, deque
from .contracts import StrategyKind, CognitiveOperation, KnowledgeForm, ScoreComponent
from .common import build_assessment, confidence_from_evidence, evidence_ids, fraction, runtime_blockers

def _acyclic(edges):
    nodes={e.cause_id for e in edges}|{e.effect_id for e in edges};ind={n:0 for n in nodes};adj=defaultdict(list)
    for e in edges:adj[e.cause_id].append(e.effect_id);ind[e.effect_id]+=1
    q=deque(sorted(n for n,d in ind.items() if d==0));seen=0
    while q:
        n=q.popleft();seen+=1
        for x in sorted(adj[n]):ind[x]-=1;q.append(x) if ind[x]==0 else None
    return seen==len(nodes)

def assess(bundle):
    bundle.validate();signals=bundle.causal_edges;targets=[o for o in bundle.objectives if CognitiveOperation.INTERVENE in o.cognitive_operations or KnowledgeForm.CAUSAL in o.knowledge_forms]
    target_ids={o.objective_id for o in targets};covered=target_ids & {s.objective_id for s in signals};nodes={e.cause_id for e in signals}|{e.effect_id for e in signals};avg_strength=(sum(e.evidence_strength for e in signals)/len(signals)) if signals else 0
    blockers=[]
    if not targets:blockers.append('no_causal_or_intervention_objective')
    if not signals:blockers.append('no_grounded_causal_edges')
    if targets and covered!=target_ids:blockers.append('incomplete_target_objective_coverage')
    if signals and not _acyclic(signals):blockers.append('causal_cycle_requires_explicit_dynamic_system_model')
    required=('semantic_visuals','stateful_interaction','semantic_motion','graph_runtime','branching_runtime','purposeful_camera');blockers+=runtime_blockers(bundle.runtime,required)
    comps=(ScoreComponent('objective_fit',fraction(len(covered),len(target_ids)),4,'Coverage of causal/intervention objectives'),ScoreComponent('graph_depth',fraction(len(signals),max(1,len(nodes)-1)),2,'Causal graph has enough directed structure'),ScoreComponent('evidence_strength',avg_strength,4,'Average evidence strength on causal edges'),ScoreComponent('intervention_support',1.0 if signals and all(e.intervention_supported for e in signals) else 0.0,3,'Edges are valid for learner interventions'))
    return build_assessment(strategy=StrategyKind.CAUSAL_SYSTEM,eligible=not blockers,components=comps,coverage=tuple(covered),blockers=tuple(blockers),strengths=('intervention_reasoning','causal_graph_exploration','counterfactual_ready') if signals else (),runtime_required=required,design_requirements=('animate_propagation_of_interventions','distinguish_correlation_from_causation','camera_follows_relevant_causal_path','show_delays_or_feedback_only_when_modelled','never_infer_unproven_causal_edge'),evidence_refs=evidence_ids([s.provenance for s in signals]+[o.provenance for o in targets]),confidence=confidence_from_evidence(len(signals),fraction(len(covered),len(target_ids)),0.55))
