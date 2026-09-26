import unittest,tempfile,json
from pathlib import Path
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.build_runtime_engine.workspace import build_workspace
from bie.game_engine.build_runtime_engine.integrity import verify_package
from bie.game_engine.build_runtime_engine.errors import GameBuildError
class H3Manifest(unittest.TestCase):
 def test_self_hash_verifies(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   w=build_workspace(c,a,Path(td));r=verify_package(Path(td)/'dist',w.manifest);self.assertEqual(r['manifest_payload_sha256'],w.manifest.manifest_payload_sha256);self.assertTrue(r['passed'])
 def test_manifest_tamper_rejected(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   w=build_workspace(c,a,Path(td));p=Path(td)/'dist/build-manifest.json';d=json.loads(p.read_text());d['entrypoint']='runtime/evil.html';p.write_text(json.dumps(d))
   with self.assertRaisesRegex(GameBuildError,'SELF_MANIFEST_TAMPER'):verify_package(Path(td)/'dist',w.manifest)
 def test_untracked_file_rejected(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   w=build_workspace(c,a,Path(td));(Path(td)/'dist/evil.txt').write_text('x')
   with self.assertRaisesRegex(GameBuildError,'UNTRACKED_FILE'):verify_package(Path(td)/'dist',w.manifest)
 def test_manifest_schema_v2(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:self.assertEqual(build_workspace(c,a,Path(td)).manifest.schema_version,'bie.game.runtime-package/2')
