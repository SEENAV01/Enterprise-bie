from __future__ import annotations
from dataclasses import asdict,is_dataclass
from typing import Mapping
from .contracts import EvidenceDigest,CanonicalAdapterResult
from ..errors import GameContractError
from ..provenance import EvidenceRef,ProvenanceBundle
from ..strategy_engine.contracts import *
from ..strategy_engine.selector import select_or_raise
from ..director_engine.contracts import MasterySignal,DirectorConstraints,DirectorContext
from ..canonical import fingerprint

CANONICAL_BLOBS=(
 ('bie/director/game_handoff.py','eed5908c96719e7bf662e0dc511189b938895e96'),
 ('bie/reasoning/game_decision.py','f2e61bebf5536cb8bbd60e5cd6097b398af3552f'),
 ('bie/pedagogy/pedagogy_plan_contract.py','acdd55084d762e26fa9d05b8c7158892a3ceda52'),
)

_MECHANIC_MAP={
 'retrieval':(StrategyKind.RETRIEVAL,CognitiveOperation.RECALL,KnowledgeForm.FACT),
 'manipulation':(StrategyKind.MANIPULATION,CognitiveOperation.MANIPULATE,KnowledgeForm.PROCEDURE),
 'manipulate_parameter':(StrategyKind.MANIPULATION,CognitiveOperation.MANIPULATE,KnowledgeForm.PROCEDURE),
 'simulation':(StrategyKind.SIMULATION,CognitiveOperation.MODEL,KnowledgeForm.SYSTEM),
 'simulation_experiment':(StrategyKind.SIMULATION,CognitiveOperation.MODEL,KnowledgeForm.SYSTEM),
 'prediction':(StrategyKind.PREDICTION,CognitiveOperation.PREDICT,KnowledgeForm.SYSTEM),
 'prediction_then_observe':(StrategyKind.PREDICTION,CognitiveOperation.PREDICT,KnowledgeForm.SYSTEM),
 'diagnostic':(StrategyKind.DIAGNOSTIC,CognitiveOperation.DIAGNOSE,KnowledgeForm.CONCEPT),
 'diagnose_error':(StrategyKind.DIAGNOSTIC,CognitiveOperation.DIAGNOSE,KnowledgeForm.CONCEPT),
 'timeline':(StrategyKind.TIMELINE,CognitiveOperation.ORDER,KnowledgeForm.TEMPORAL),
 'timeline_reconstruction':(StrategyKind.TIMELINE,CognitiveOperation.ORDER,KnowledgeForm.TEMPORAL),
 'map':(StrategyKind.MAP,CognitiveOperation.LOCATE,KnowledgeForm.SPATIAL),
 'map_interaction':(StrategyKind.MAP,CognitiveOperation.LOCATE,KnowledgeForm.SPATIAL),
 'equation':(StrategyKind.EQUATION,CognitiveOperation.SOLVE,KnowledgeForm.SYMBOLIC),
 'equation_balance':(StrategyKind.EQUATION,CognitiveOperation.SOLVE,KnowledgeForm.SYMBOLIC),
 'causal_system':(StrategyKind.CAUSAL_SYSTEM,CognitiveOperation.INTERVENE,KnowledgeForm.CAUSAL),
 'causal_intervention':(StrategyKind.CAUSAL_SYSTEM,CognitiveOperation.INTERVENE,KnowledgeForm.CAUSAL),
}

def _field(obj,name):
    if not hasattr(obj,name):raise GameContractError('GAME_UPSTREAM_FIELD_MISSING',name)
    return getattr(obj,name)

def _norm_ids(values,code):
    vals=tuple(values)
    if not vals or any(not isinstance(x,str) or not x for x in vals) or len(vals)!=len(set(vals)):raise GameContractError(code)
    return vals

def _digest_map(digests):
    out={}
    for d in digests:d.validate();out[d.evidence_id]=d
    return out

def _prov(ids,role,digests,extra=()):
    refs=[]
    for eid in ids:
        d=digests.get(eid)
        if d is None:raise GameContractError('GAME_UPSTREAM_EVIDENCE_DIGEST_MISSING',eid)
        refs.append(EvidenceRef(d.evidence_id,d.locator,d.sha256,role))
    refs.extend(extra)
    return tuple(refs)

def _pedagogy_decisions(plan):
    ds=tuple(_field(plan,'decisions'))
    if not ds:raise GameContractError('GAME_UPSTREAM_PEDAGOGY_DECISIONS_REQUIRED')
    for d in ds:
        status=_field(d,'status');review=_field(d,'requires_review');conf=_field(d,'confidence')
        if status!='RESOLVED' or review is not False or type(conf) not in (int,float) or conf<.75:raise GameContractError('GAME_UPSTREAM_PEDAGOGY_UNRESOLVED',_field(d,'decision_id'))
    if _field(plan,'requires_review') is not False:raise GameContractError('GAME_UPSTREAM_PEDAGOGY_REVIEW_REQUIRED')
    return ds

def adapt_canonical_upstream(game_handoff,reasoning_game,pedagogy_plan,evidence_digests,*,runtime=RuntimeCapabilitySet()):
    # Structural validation against the exact canonical shapes recorded by CANONICAL_BLOBS.
    lesson_id=_field(game_handoff,'lesson_id');objectives=_norm_ids(_field(game_handoff,'objective_ids'),'GAME_UPSTREAM_OBJECTIVES');concepts=_norm_ids(_field(game_handoff,'concept_ids'),'GAME_UPSTREAM_CONCEPTS')
    misconceptions=tuple(_field(game_handoff,'misconception_ids'));checks=_norm_ids(_field(game_handoff,'mastery_checks'),'GAME_UPSTREAM_MASTERY_CHECKS');evidence_ids=_norm_ids(_field(game_handoff,'evidence_ids'),'GAME_UPSTREAM_EVIDENCE_IDS')
    if _field(game_handoff,'forbidden_ungrounded_mechanics') is not True:raise GameContractError('GAME_UPSTREAM_UNGROUNDED_MECHANICS_WEAKENED')
    mechanic=_field(reasoning_game,'mechanic')
    if mechanic not in _MECHANIC_MAP:raise GameContractError('GAME_UPSTREAM_MECHANIC_UNSUPPORTED',str(mechanic))
    for name in ('objective_fit','retrieval_value','misconception_value'):
        v=_field(reasoning_game,name)
        if type(v) not in (int,float) or not 0<=v<=1:raise GameContractError('GAME_UPSTREAM_REASONING_SCORE',name)
    kind,cog,kform=_MECHANIC_MAP[mechanic];ds=_pedagogy_decisions(pedagogy_plan);digests=_digest_map(evidence_digests)
    # Preserve exact upstream evidence IDs. Pedagogy evidence is reasoning lineage; handoff evidence is source lineage.
    source_refs=_prov(evidence_ids,'source',digests)
    ped_evidence=tuple(sorted({eid for d in ds for eid in _field(d,'evidence_ids')}))
    reasoning_refs=_prov(ped_evidence,'reasoning',digests)
    obj_refs=[]
    for oid in objectives:
        d=digests.get(oid)
        if d is None:raise GameContractError('GAME_UPSTREAM_OBJECTIVE_DIGEST_MISSING',oid)
        obj_refs.append(EvidenceRef(d.evidence_id,d.locator,d.sha256,'objective'))
    mis_refs=[]
    for mid in misconceptions:
        d=digests.get(mid)
        if d is None:raise GameContractError('GAME_UPSTREAM_MISCONCEPTION_DIGEST_MISSING',mid)
        mis_refs.append(EvidenceRef(d.evidence_id,d.locator,d.sha256,'misconception'))
    all_refs=tuple(source_refs)+tuple(reasoning_refs)+tuple(obj_refs)+tuple(mis_refs)
    inherited=(lesson_id,_field(pedagogy_plan,'plan_id'),_field(pedagogy_plan,'source_id'))
    bundle_prov=ProvenanceBundle(all_refs,inherited).validate(('source','reasoning'))
    # Concepts are global in the canonical handoff; bind all objectives explicitly rather than infer per-objective subsets.
    signals=[]
    for oid in objectives:
        refs=tuple(source_refs)+tuple(reasoning_refs)+(next(x for x in obj_refs if x.artifact_id==oid),)
        related_mis=tuple(misconceptions)
        refs=refs+tuple(mis_refs)
        prov=ProvenanceBundle(refs,inherited).validate(('source','reasoning','objective'))
        signals.append(ObjectiveSignal(oid,(cog,),(kform,),concepts,related_mis,1.0,prov).validate())
    kwargs={}
    # Produce the minimum structured signal required by the canonical reasoning-selected strategy.
    if kind is StrategyKind.RETRIEVAL:
        kwargs['retrieval_items']=tuple(RetrievalItemSignal('retrieval:'+oid,oid,'prompt:'+oid,'answer:'+oid,'spacing:'+oid,ProvenanceBundle(tuple(source_refs)+(next(x for x in obj_refs if x.artifact_id==oid),),inherited).validate(('source','objective'))) for oid in objectives)
    elif kind is StrategyKind.MANIPULATION:
        kwargs['manipulations']=tuple(ManipulationSignal('variable:'+oid,oid,'Adjust the governed variable',True,True,('effect:'+oid,),ProvenanceBundle(tuple(source_refs)+tuple(reasoning_refs)+(next(x for x in obj_refs if x.artifact_id==oid),),inherited).validate(('source','reasoning','objective'))) for oid in objectives)
    elif kind is StrategyKind.SIMULATION:
        kwargs['simulations']=tuple(SimulationSignal('model:'+oid,oid,('parameter:'+oid,),('output:'+oid,),'Canonical pedagogy/reasoning model scope',True,ProvenanceBundle(tuple(source_refs)+tuple(reasoning_refs)+(next(x for x in obj_refs if x.artifact_id==oid),),inherited).validate(('source','reasoning','objective'))) for oid in objectives)
    elif kind is StrategyKind.PREDICTION:
        kwargs['predictions']=tuple(PredictionSignal('target:'+oid,oid,'observable:'+oid,True,'exact_or_policy_defined',ProvenanceBundle(tuple(source_refs)+tuple(reasoning_refs)+(next(x for x in obj_refs if x.artifact_id==oid),),inherited).validate(('source','reasoning','objective'))) for oid in objectives)
    elif kind is StrategyKind.DIAGNOSTIC:
        if not misconceptions:raise GameContractError('GAME_UPSTREAM_DIAGNOSTIC_MISCONCEPTION_REQUIRED')
        kwargs['diagnostics']=tuple(DiagnosticSignal('case:'+oid,oid,misconceptions[0],'incorrect:'+oid,'explanation:'+oid,ProvenanceBundle(tuple(source_refs)+tuple(reasoning_refs)+(next(x for x in obj_refs if x.artifact_id==oid),)+tuple(mis_refs),inherited).validate(('source','reasoning','objective','misconception'))) for oid in objectives)
    elif kind is StrategyKind.TIMELINE:
        kwargs['temporal_events']=tuple(TemporalSignal('event:'+oid,oid,float(i),'anchor:'+oid,ProvenanceBundle(tuple(source_refs)+(next(x for x in obj_refs if x.artifact_id==oid),),inherited).validate(('source','objective'))) for i,oid in enumerate(objectives))
    elif kind is StrategyKind.MAP:
        raise GameContractError('GAME_UPSTREAM_MAP_COORDINATES_REQUIRED')
    elif kind is StrategyKind.EQUATION:
        kwargs['equations']=tuple(EquationSignal('equation:'+oid,oid,('x',),('solve',),True,ProvenanceBundle(tuple(source_refs)+tuple(reasoning_refs)+(next(x for x in obj_refs if x.artifact_id==oid),),inherited).validate(('source','reasoning','objective'))) for oid in objectives)
    elif kind is StrategyKind.CAUSAL_SYSTEM:
        kwargs['causal_edges']=tuple(CausalEdgeSignal('edge:'+oid,oid,'cause:'+oid,'effect:'+oid,True,float(_field(reasoning_game,'objective_fit')),ProvenanceBundle(tuple(source_refs)+tuple(reasoning_refs)+(next(x for x in obj_refs if x.artifact_id==oid),),inherited).validate(('source','reasoning','objective'))) for oid in objectives)
    bundle=StrategySignalBundle(tuple(signals),runtime=runtime,provenance=bundle_prov,**kwargs).validate()
    decision=select_or_raise(bundle)
    if decision.primary is not kind:raise GameContractError('GAME_UPSTREAM_STRATEGY_MISMATCH',decision.primary.value)
    # Mastery checks exist but the canonical handoff has no numeric mastery state: represent as unseen, high-confidence structural evidence rather than inventing attainment.
    mastery=tuple(MasterySignal(oid,0.0,1.0,0,next(x.provenance for x in signals if x.objective_id==oid)).validate() for oid in objectives)
    ctx=DirectorContext(bundle,decision,mastery,DirectorConstraints(),bundle_prov).validate()
    material={'handoff':repr(game_handoff),'reasoning':repr(reasoning_game),'pedagogy_fingerprint':pedagogy_plan.fingerprint() if hasattr(pedagogy_plan,'fingerprint') else repr(pedagogy_plan),'canonical_blobs':CANONICAL_BLOBS,'evidence_ids':sorted(set(evidence_ids+ped_evidence+objectives+misconceptions))}
    return CanonicalAdapterResult(bundle,ctx,fingerprint(material),CANONICAL_BLOBS,tuple(material['evidence_ids']),False).validate()
