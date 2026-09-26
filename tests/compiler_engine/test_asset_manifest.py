import unittest,json
from dataclasses import replace
from bie.game_engine.compiler_engine.asset_manifest import compile_asset_manifest
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.compiler_engine.errors import GameCompilerError
class AssetManifestTests(unittest.TestCase):
 def test_required_audio_asset_resolved(self):
  d=json.loads(compile_asset_manifest(compiler_context()).content);self.assertTrue(d['all_required_resolved']);self.assertEqual(d['assets'][0]['asset_ref'],'asset:sfx:success')
 def test_missing_asset_fails_closed(self):
  with self.assertRaises(GameCompilerError):compile_asset_manifest(replace(compiler_context(),assets={}))
