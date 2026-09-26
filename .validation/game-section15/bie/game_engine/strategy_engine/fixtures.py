from __future__ import annotations
from .contracts import *
from ..provenance import EvidenceRef, ProvenanceBundle

def evidence():
    h='1'*64
    return ProvenanceBundle((
      EvidenceRef('source:book','page:10',h,'source'),
      EvidenceRef('reason:strategy','decision:1',h,'reasoning'),
      EvidenceRef('objective:strategy','lo:1',h,'objective'),
      EvidenceRef('misconception:strategy','mis:1',h,'misconception'),
    ))

def objective(objective_id, ops, forms, misconceptions=()):
    return ObjectiveSignal(objective_id,tuple(ops),tuple(forms),(f'concept:{objective_id}',),tuple(misconceptions),1.0,evidence())

def rich_bundle():
    objs=(
      objective('obj:recall',(CognitiveOperation.RECALL,),(KnowledgeForm.FACT,)),
      objective('obj:manip',(CognitiveOperation.MANIPULATE,),(KnowledgeForm.PROCEDURE,)),
      objective('obj:sim',(CognitiveOperation.MODEL,),(KnowledgeForm.SYSTEM,)),
      objective('obj:predict',(CognitiveOperation.PREDICT,),(KnowledgeForm.SYSTEM,)),
      objective('obj:diag',(CognitiveOperation.DIAGNOSE,),(KnowledgeForm.CONCEPT,),('mis:diag',)),
      objective('obj:time',(CognitiveOperation.ORDER,),(KnowledgeForm.TEMPORAL,)),
      objective('obj:map',(CognitiveOperation.LOCATE,),(KnowledgeForm.SPATIAL,)),
      objective('obj:eq',(CognitiveOperation.SOLVE,),(KnowledgeForm.SYMBOLIC,)),
      objective('obj:causal',(CognitiveOperation.INTERVENE,),(KnowledgeForm.CAUSAL,)),
    )
    prov=evidence()
    return StrategySignalBundle(
      objs,
      retrieval_items=(RetrievalItemSignal('ri:1','obj:recall','prompt:1','answer:1','space:1',prov),RetrievalItemSignal('ri:2','obj:recall','prompt:2','answer:2','space:2',prov)),
      manipulations=(ManipulationSignal('x','obj:manip','adjust x',True,True,('effect:position',),prov),),
      simulations=(SimulationSignal('model:1','obj:sim',('param:a','param:b'),('out:y',),'Grounded classroom model, valid only in declared parameter bounds.',True,prov),),
      predictions=(PredictionSignal('pred:1','obj:predict','observable:y',True,'absolute_error',prov),),
      diagnostics=(DiagnosticSignal('case:1','obj:diag','mis:diag','state:wrong','explain:right',prov),),
      temporal_events=(TemporalSignal('event:1','obj:time',1,'source:t1',prov),TemporalSignal('event:2','obj:time',2,'source:t2',prov),TemporalSignal('event:3','obj:time',3,'source:t3',prov)),
      geo_entities=(GeoSignal('geo:a','obj:map',28.6,77.2,'source:geo:a',prov),GeoSignal('geo:b','obj:map',28.45,77.03,'source:geo:b',prov)),
      equations=(EquationSignal('eq:1','obj:eq',('x','y'),('add','divide'),True,prov),),
      causal_edges=(CausalEdgeSignal('edge:1','obj:causal','force','acceleration',True,.95,prov),CausalEdgeSignal('edge:2','obj:causal','acceleration','velocity',True,.9,prov)),
      runtime=RuntimeCapabilitySet(),provenance=prov)


def single_strategy_bundle(kind:StrategyKind):
    b=rich_bundle(); mapping={
      StrategyKind.RETRIEVAL:'obj:recall',StrategyKind.MANIPULATION:'obj:manip',StrategyKind.SIMULATION:'obj:sim',StrategyKind.PREDICTION:'obj:predict',StrategyKind.DIAGNOSTIC:'obj:diag',StrategyKind.TIMELINE:'obj:time',StrategyKind.MAP:'obj:map',StrategyKind.EQUATION:'obj:eq',StrategyKind.CAUSAL_SYSTEM:'obj:causal'}
    oid=mapping[kind]; objs=tuple(o for o in b.objectives if o.objective_id==oid)
    kwargs=dict(objectives=objs,retrieval_items=(),manipulations=(),simulations=(),predictions=(),diagnostics=(),temporal_events=(),geo_entities=(),equations=(),causal_edges=(),runtime=b.runtime,provenance=b.provenance)
    field={StrategyKind.RETRIEVAL:'retrieval_items',StrategyKind.MANIPULATION:'manipulations',StrategyKind.SIMULATION:'simulations',StrategyKind.PREDICTION:'predictions',StrategyKind.DIAGNOSTIC:'diagnostics',StrategyKind.TIMELINE:'temporal_events',StrategyKind.MAP:'geo_entities',StrategyKind.EQUATION:'equations',StrategyKind.CAUSAL_SYSTEM:'causal_edges'}[kind]
    kwargs[field]=getattr(b,field)
    return StrategySignalBundle(**kwargs)
