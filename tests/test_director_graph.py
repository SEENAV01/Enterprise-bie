import unittest
from dataclasses import replace
from bie.game_engine.director_engine.fixtures import director_context
from bie.game_engine.director_engine.planner import plan_experience
from bie.game_engine.director_engine.graph import validate_level_graph,validate_progression
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_valid_graph(self):self.assertEqual(validate_progression(plan_experience(director_context()).levels),('level:01',))
 def test_missing_parent_fails(self):
  p=plan_experience(director_context());l=replace(p.levels[0],prerequisite_level_ids=('missing',))
  with self.assertRaisesRegex(GameContractError,'MISSING_PREREQUISITE'):validate_level_graph((l,))
 def test_self_edge_fails(self):
  p=plan_experience(director_context());l=replace(p.levels[0],prerequisite_level_ids=(p.levels[0].level_id,))
  with self.assertRaises(GameContractError):validate_level_graph((l,))
 def test_cycle_fails(self):
  from bie.game_engine.director_engine.contracts import LevelNode,LevelRole,MechanicKind
  a=LevelNode('a',LevelRole.PRACTICE,('obj:a',),MechanicKind.RETRIEVAL,30,('b',),'a');b=LevelNode('b',LevelRole.PRACTICE,('obj:b',),MechanicKind.RETRIEVAL,30,('a',),'b')
  with self.assertRaisesRegex(GameContractError,'CYCLE'):validate_level_graph((a,b))
