from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
from ..strategy_engine.contracts import StrategyKind
from ..strategy_engine.fixtures import rich_bundle,single_strategy_bundle
from ..director_engine.fixtures import director_context
from ..director_engine.planner import plan_experience
from ..fixtures import sample_document
from ..compiler_engine.fixtures import compiler_context
from ..compiler_engine.pipeline import compile_game
from ..build_runtime_engine.fixtures import build_inputs
from ..build_runtime_engine.pipeline import build_runtime_package
from ..state_engine.reachability import StateNode,StateEdge,TransitionSystem
ALL_STRATEGIES=tuple(StrategyKind)
def all_strategy_plans():return tuple(plan_experience(director_context(k)) for k in ALL_STRATEGIES)
def diagnostic_plan():return plan_experience(director_context(StrategyKind.DIAGNOSTIC))
def healthy_transition_system():
    nodes=(StateNode('s0','sha256:'+'0'*64),StateNode('s1','sha256:'+'1'*64),StateNode('s2','sha256:'+'2'*64,True))
    edges=(StateEdge('e01','s0','s1','transition:t1'),StateEdge('e12','s1','s2','transition:t2'))
    return TransitionSystem(nodes,edges,100,False).validate()
def dead_end_transition_system():
    nodes=(StateNode('s0','sha256:'+'0'*64),StateNode('s1','sha256:'+'1'*64),StateNode('goal','sha256:'+'2'*64,True),StateNode('dead','sha256:'+'3'*64))
    edges=(StateEdge('e01','s0','s1','transition:t1'),StateEdge('e1g','s1','goal','transition:t2'),StateEdge('e1d','s1','dead','transition:td'))
    return TransitionSystem(nodes,edges,100,False).validate()
@lru_cache(maxsize=1)
def compiled_bundle():return compile_game(compiler_context())
@lru_cache(maxsize=1)
def runtime_result():
    ctx,assets=build_inputs()
    with TemporaryDirectory(prefix='bie-game-qa-runtime-') as td:return build_runtime_package(ctx,assets,Path(td))
