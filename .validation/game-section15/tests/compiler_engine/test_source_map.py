import unittest,json
from bie.game_engine.compiler_engine.source_map import build_source_map
from bie.game_engine.compiler_engine.fixtures import compiler_context
class SourceMapTests(unittest.TestCase):
 def test_level_and_challenge_bound(self):
  d=json.loads(build_source_map(compiler_context()).content);refs={x['runtime_ref'] for x in d['bindings']};self.assertIn('level:1',refs);self.assertIn('challenge:motion',refs)
