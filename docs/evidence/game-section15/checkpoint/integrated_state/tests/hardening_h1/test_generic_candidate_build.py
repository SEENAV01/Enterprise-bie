import unittest,inspect
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.build_runtime_engine.interaction_simulation import simulate
from bie.game_engine.build_runtime_engine.deterministic_replay import verify_deterministic_replay
from bie.game_engine.build_runtime_engine.action_script import derive_candidate_script
class GenericCandidateBuildTests(unittest.TestCase):
 def setUp(self):self.ctx,_=build_inputs();self.bundle=compile_game(self.ctx)
 def test_script_derived_from_candidate(self):
  s=derive_candidate_script(self.ctx);self.assertTrue(s);self.assertIn(s[0].action_id,{a.action_id for a in self.ctx.document.experiences[0].levels[0].interaction.actions})
 def test_simulation_uses_candidate(self):self.assertTrue(simulate(self.ctx,self.bundle).compiled_event_present)
 def test_replay_uses_candidate(self):self.assertTrue(verify_deterministic_replay(self.ctx).identical_second_run)
 def test_no_fixture_imports_in_runtime_modules(self):
  import bie.game_engine.build_runtime_engine.interaction_simulation as a,bie.game_engine.build_runtime_engine.deterministic_replay as b
  self.assertNotIn('sample_document',inspect.getsource(a));self.assertNotIn('sample_document',inspect.getsource(b));self.assertNotIn('drag_command',inspect.getsource(b))
