from dataclasses import replace
from pathlib import Path
from bie.game_engine.qa_engine.fixtures import *
from bie.game_engine.qa_engine.contracts import GateStatus,enforce
from bie.game_engine.qa_engine.policy import GameQAPolicy
from bie.game_engine.strategy_engine.fixtures import rich_bundle,single_strategy_bundle
from bie.game_engine.strategy_engine.contracts import StrategyKind
from bie.game_engine.director_engine.planner import plan_experience
from bie.game_engine.director_engine.fixtures import director_context
from bie.game_engine.fixtures import sample_document
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.compiler_engine.pipeline import compile_game
ROOT=Path(__file__).resolve().parents[2]
def assert_pass(tc,r):tc.assertIs(r.status,GateStatus.PASS);tc.assertFalse(r.product_accepted);tc.assertTrue(r.deterministic);tc.assertTrue(r.result_fingerprint.startswith('sha256:'));enforce(r)
