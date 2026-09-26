import unittest,tempfile,hashlib
from pathlib import Path
from dataclasses import replace
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.build_runtime_engine.workspace import build_workspace
from bie.game_engine.build_runtime_engine.integrity import verify_package,verify_compiler_binding
from bie.game_engine.build_runtime_engine.errors import GameBuildError
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.compiler_engine.contracts import artifact
class Integrity(unittest.TestCase):
 def test_compiler_receipt_binding(self):
  c,_=build_inputs();self.assertTrue(verify_compiler_binding(c,compile_game(c)))
 def test_tampered_compiler_artifact_set_rejected(self):
  c,_=build_inputs();b=compile_game(c);a=b.artifacts[0];bad=artifact(a.kind,a.path,a.media_type,a.content+'x',a.source_refs);tb=replace(b,artifacts=(bad,*b.artifacts[1:]))
  with self.assertRaisesRegex(GameBuildError,'ARTIFACT_MISMATCH'):verify_compiler_binding(c,tb)
 def test_fresh_package_verifies(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   w=build_workspace(c,a,Path(td));self.assertTrue(verify_package(Path(td)/'dist',w.manifest)['passed'])
 def test_tampered_package_file_rejected(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   w=build_workspace(c,a,Path(td));p=Path(td)/'dist/runtime/entry.js';p.write_text(p.read_text()+'//tamper')
   with self.assertRaisesRegex(GameBuildError,'PACKAGE_ARTIFACT_TAMPER'):verify_package(Path(td)/'dist',w.manifest)
 def test_missing_package_file_rejected(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   w=build_workspace(c,a,Path(td));(Path(td)/'dist/runtime/entry.js').unlink()
   with self.assertRaisesRegex(GameBuildError,'PACKAGE_ARTIFACT_MISSING'):verify_package(Path(td)/'dist',w.manifest)
