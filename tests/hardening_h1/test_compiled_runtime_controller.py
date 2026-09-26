import unittest,json
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.compiler_engine.pipeline import compile_game
class ControllerCompileTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.b=compile_game(compiler_context());cls.by={a.path:a for a in cls.b.artifacts}
 def test_runtime_controller_artifact_present(self):self.assertIn('runtime/runtime-controller.ts',self.by)
 def test_controller_executes_all_runtime_programs(self):
  s=self.by['runtime/runtime-controller.ts'].content
  for needle in ('ruleFunctions','scoringProgram','feedbackProgram','adaptationFunctions','sanitizeTelemetry','applySemanticState','addEventListener','dispatch('):self.assertIn(needle,s)
 def test_interaction_program_contains_authoritative_routes(self):
  s=self.by['runtime/interactions.ts'].content;self.assertIn('authoritative_state_router',s);self.assertIn('rule:move',s);self.assertIn('drag_and_drop',s)
 def test_manifest_binds_controller(self):
  m=json.loads(self.by['runtime/manifest.json'].content);self.assertIn(['runtime/bootstrap.js','runtime/runtime-controller.js'],m['dependency_edges']);self.assertIn('runtime/runtime-controller.js',m['expected_build_outputs'])
 def test_generated_runtime_has_no_eval(self):
  text='\n'.join(a.content for a in self.b.artifacts);self.assertNotIn('eval(',text);self.assertNotIn('new Function',text)
 def test_renderer_has_all_visual_kinds(self):
  from bie.game_engine.visual import VisualKind
  import bie.game_engine.compiler_engine.react_runtime as rr
  self.assertEqual(set(rr._GLYPH),{v.value for v in VisualKind})
