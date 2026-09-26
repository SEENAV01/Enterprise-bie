from __future__ import annotations
from dataclasses import dataclass,replace
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
from bie.game_engine.director_engine.fixtures import director_context
from bie.game_engine.director_engine.planner import plan_experience
from bie.game_engine.strategy_engine.contracts import StrategyKind
from bie.game_engine.visual import VisualKind
from bie.game_engine.handoff_engine.contracts import *
from bie.game_engine.handoff_engine.materializer import materialize,to_compiler_context
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.build_runtime_engine.pipeline import build_runtime_package
from bie.game_engine.qa_engine.candidate import CandidateGameEvidence,CandidateBenchmarkRecord
from bie.game_engine.qa_engine.fixtures import healthy_transition_system
ROOT=Path(__file__).resolve().parents[2]

def sha(seed):return hashlib.sha256(seed.encode()).hexdigest()

def materialization_inputs(kind=StrategyKind.MANIPULATION):
    ctx=director_context(kind);plan=plan_experience(ctx);texts={};visuals={}
    for o in plan.objective_assignments:
        texts[o.objective_id]=ObjectiveTextMaterial(o.objective_id,'Interactive '+o.objective_id,'Learn '+o.objective_id+' through meaningful interaction','Challenge '+o.objective_id,'Manipulate the governed representation to satisfy the objective.','Correct. The state change satisfies the objective.','Not yet. Re-examine the evidence and state.','The feedback is grounded in the objective evidence.','Interactive representation for '+o.objective_id)
        visuals[o.objective_id]=ObjectiveVisualMaterial(o.objective_id,VisualKind.OBJECT,'learner_controlled_model',next(r.artifact_id for r in ctx.provenance.refs if r.role=='source'),'Semantic object controlled by the learner')
    return MaterializationInputs(plan,ctx.signals,texts,visuals,ctx.provenance)

@lru_cache(maxsize=1)
def materialized():return materialize(materialization_inputs())
@lru_cache(maxsize=1)
def compiler_context():return to_compiler_context(materialized())
@lru_cache(maxsize=1)
def compiled():return compile_game(compiler_context())
@lru_cache(maxsize=1)
def runtime():
    with TemporaryDirectory(prefix='bie-h2-runtime-') as td:return build_runtime_package(compiler_context(),{},Path(td))

def benchmarks():
    fp=materialized().document.fingerprint();pf=materialization_inputs().plan.plan_fingerprint;refs=materialized().receipt.evidence_refs
    rows=[('physics','simulation','simulation_experiment'),('chemistry','manipulation','manipulate_parameter'),('biology','diagnostic','diagnose_error'),('mathematics','equation','equation_balance'),('history','timeline','timeline_reconstruction'),('geography','map','map_interaction'),('economics','causal_system','causal_intervention'),('polity','retrieval','retrieval')]
    return tuple(CandidateBenchmarkRecord(d,s,(m,),m,pf,fp,refs).validate() for d,s,m in rows)

@lru_cache(maxsize=1)
def candidate():
    system=healthy_transition_system();m=materialized();ctx=materialization_inputs()
    return CandidateGameEvidence('candidate:h2',ctx.signals,(ctx.plan,),m.document,compiler_context(),compiled(),runtime(),system,'s0',(('challenge:goal','s2'),),('s2',),benchmarks(),ROOT/'bie/game_engine',m.receipt.evidence_refs,False).validate()

# Exact-shape proxies for the canonical dependencies audited at current main.
@dataclass(frozen=True)
class GameHandoffProxy:
    lesson_id:str;objective_ids:tuple[str,...];concept_ids:tuple[str,...];misconception_ids:tuple[str,...];mastery_checks:tuple[str,...];evidence_ids:tuple[str,...];forbidden_ungrounded_mechanics:bool=True
@dataclass(frozen=True)
class GameDecisionProxy:
    mechanic:str;objective_fit:float;retrieval_value:float;misconception_value:float
@dataclass(frozen=True)
class PedagogyDecisionProxy:
    decision_id:str;kind:str;payload_id:str;evidence_ids:tuple[str,...];parent_decision_ids:tuple[str,...]=();status:str='RESOLVED';confidence:float=1.0;requires_review:bool=False
@dataclass(frozen=True)
class PedagogyPlanProxy:
    plan_id:str;source_id:str;objective_ids:tuple[str,...];lesson_ids:tuple[str,...];decisions:tuple[PedagogyDecisionProxy,...];policy_version:str;requires_review:bool=False
    def fingerprint(self):return 'sha256:'+sha(repr(self))

def canonical_inputs(*,mechanic='manipulate_parameter',review=False,confidence=1.0,status='RESOLVED'):
    gh=GameHandoffProxy('lesson:1',('obj:motion',),('concept:motion',),('mis:direction',),('mastery:motion',),('source:book',),True)
    rg=GameDecisionProxy(mechanic,.95,.4,.7)
    pd=PedagogyDecisionProxy('ped:1','teaching_mode','mode:interactive',('reason:ped',),(),status,confidence,review)
    pp=PedagogyPlanProxy('ped-plan:1','source:book',('obj:motion',),('lesson:1',),(pd,),'ped-policy:1',review)
    ids=('source:book','reason:ped','obj:motion','mis:direction')
    digests=tuple(EvidenceDigest(i,'canonical:'+i,sha(i),('source' if i=='source:book' else 'reasoning' if i=='reason:ped' else 'objective' if i=='obj:motion' else 'misconception')).validate() for i in ids)
    return gh,rg,pp,digests
