import unittest
from bie.game_engine.compiler_engine.bootstrap import compile_bootstrap
from bie.game_engine.compiler_engine.fixtures import compiler_context
class FullBootstrapTests(unittest.TestCase):
 def test_all_programs_bound(self):
  s=compile_bootstrap(compiler_context()).content
  for name in ('stateMachine','ruleMetadata','interactionProgram','scoringProgram','feedbackProgram','adaptationMetadata','telemetryProgram','sanitizeTelemetry'):self.assertIn(name,s)
 def test_bootstrap_mounts_studio_level(self):
  s=compile_bootstrap(compiler_context()).content;self.assertIn('renderGameRuntime',s);self.assertIn('mount(node)',s)
