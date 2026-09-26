import unittest
from bie.game_engine.errors import GameContractError
from bie.game_engine.state_engine.reachability import *
from bie.game_engine.state_engine.fixtures import sample_transition_system

class ReachabilityTests(unittest.TestCase):
 def test_reachable_path(self):self.assertEqual(analyze_reachability(sample_transition_system(),'s0',('s2',))['paths']['s2'],['s0','s1','s2'])
 def test_unreachable_target(self):
  s=sample_transition_system();r=analyze_reachability(s,'dead',('s2',));self.assertEqual(r['unreachable'],['s2'])
 def test_dead_end_detected(self):self.assertIn('dead',analyze_reachability(sample_transition_system(),'s0',('s2',))['dead_ends'])
 def test_terminal_not_dead_end(self):self.assertNotIn('s2',analyze_reachability(sample_transition_system(),'s0',('s2',))['dead_ends'])
 def test_missing_node_edge_fails(self):
  s=sample_transition_system();bad=TransitionSystem(s.nodes,s.edges+(StateEdge('bad','s0','missing','transition:x'),),100)
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_GRAPH_MISSING_NODE'):bad.validate()
 def test_duplicate_node_fails(self):
  s=sample_transition_system();bad=TransitionSystem(s.nodes+(s.nodes[0],),s.edges,100)
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_GRAPH_DUP_NODE'):bad.validate()
 def test_budget_enforced(self):
  s=sample_transition_system();bad=TransitionSystem(s.nodes,s.edges,2)
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_GRAPH_BUDGET'):bad.validate()
 def test_query_requires_known_start(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_GRAPH_QUERY'):analyze_reachability(sample_transition_system(),'missing',('s2',))
 def test_query_requires_target(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_GRAPH_QUERY'):analyze_reachability(sample_transition_system(),'s0',())
 def test_cycle_reported(self):
  s=sample_transition_system();cyc=TransitionSystem(s.nodes,s.edges+(StateEdge('e20','s2','s0','transition:cycle'),),100);self.assertTrue(analyze_reachability(cyc,'s0',('s2',))['cycles'])
 def test_order_deterministic(self):self.assertEqual(analyze_reachability(sample_transition_system(),'s0',('s2',)),analyze_reachability(sample_transition_system(),'s0',('s2',)))
 def test_product_acceptance_false(self):self.assertFalse(analyze_reachability(sample_transition_system(),'s0',('s2',))['product_accepted'])
