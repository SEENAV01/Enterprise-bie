import unittest,json
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.compiler_engine.fixtures import compiler_context
class PipelineSecurityTests(unittest.TestCase):
 def test_manifest_security_and_quality(self):
  b=compile_game(compiler_context());m=next(a for a in b.artifacts if a.path=='runtime/manifest.json');d=json.loads(m.content);self.assertFalse(d['security']['remote_network']);self.assertFalse(d['security']['eval']);self.assertTrue(d['quality']['studio_grade']);self.assertFalse(d['quality']['slide_deck_default'])
 def test_product_acceptance_false_everywhere(self):
  b=compile_game(compiler_context());self.assertFalse(b.product_accepted);self.assertFalse(b.receipt.product_accepted);self.assertTrue(all(not a.product_accepted for a in b.artifacts))
