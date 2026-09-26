import unittest
from bie.game_engine.compiler_engine.bootstrap import compile_bootstrap
from bie.game_engine.compiler_engine.fixtures import compiler_context
class BootstrapTests(unittest.TestCase):
 def test_bootstrap_imports_compiled_runtime_modules(self):
  s=compile_bootstrap(compiler_context()).content
  for x in ('./react-runtime','./state-machine','./interactions','./telemetry'):self.assertIn(x,s)
 def test_no_remote_or_eval(self):
  s=compile_bootstrap(compiler_context()).content;self.assertNotIn('eval(',s);self.assertNotIn('http://',s);self.assertNotIn('https://',s)
