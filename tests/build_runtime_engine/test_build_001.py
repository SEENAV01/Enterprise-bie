import unittest,tempfile,json,hashlib
from pathlib import Path
from dataclasses import replace
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.build_runtime_engine.workspace import build_workspace
from bie.game_engine.build_runtime_engine.contracts import BuildPolicy
from bie.game_engine.build_runtime_engine.errors import GameBuildError
class Build001(unittest.TestCase):
 def test_real_typescript_build_and_manifest(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   w=build_workspace(c,a,Path(td));self.assertTrue((Path(td)/'dist/runtime/bootstrap.js').is_file());self.assertTrue((Path(td)/'dist/runtime/entry.js').is_file());self.assertTrue(w.manifest.deterministic);self.assertFalse(w.manifest.product_accepted)
 def test_all_manifest_hashes_match(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   w=build_workspace(c,a,Path(td))
   for x in w.manifest.artifacts:self.assertEqual(hashlib.sha256((Path(td)/'dist'/x.path).read_bytes()).hexdigest(),x.sha256)
 def test_imports_linked_for_browser(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   build_workspace(c,a,Path(td));s=(Path(td)/'dist/runtime/bootstrap.js').read_text();self.assertIn('./react-runtime.js',s);self.assertNotIn('from "./react-runtime"',s)
 def test_missing_asset_bytes_fails(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaisesRegex(GameBuildError,'GAME_BUILD_ASSET_BYTES_MISSING'):build_workspace(c,{},Path(td))
 def test_wrong_asset_hash_fails(self):
  c,a=build_inputs();bad={k:b'bad' for k in a}
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaisesRegex(GameBuildError,'GAME_BUILD_ASSET_HASH_MISMATCH'):build_workspace(c,bad,Path(td))
 def test_nonempty_workspace_rejected(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   Path(td,'x').write_text('x')
   with self.assertRaisesRegex(GameBuildError,'GAME_BUILD_WORKSPACE_NOT_EMPTY'):build_workspace(c,a,Path(td))
 def test_package_fingerprint_repeatable(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as x,tempfile.TemporaryDirectory() as y:self.assertEqual(build_workspace(c,a,Path(x)).manifest.package_fingerprint,build_workspace(c,a,Path(y)).manifest.package_fingerprint)
 def test_external_network_policy_forbidden(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaisesRegex(GameBuildError,'GAME_BUILD_POLICY_WEAKENED'):build_workspace(c,a,Path(td),BuildPolicy(allow_external_network=True))
 def test_deployment_security_headers_include_frame_ancestors(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   build_workspace(c,a,Path(td));h=json.loads((Path(td)/'dist/runtime/security-headers.json').read_text());self.assertIn("frame-ancestors 'none'",h['Content-Security-Policy']);self.assertEqual(h['X-Content-Type-Options'],'nosniff')
 def test_entrypoint_is_manifested(self):
  c,a=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   m=build_workspace(c,a,Path(td)).manifest;self.assertEqual(m.entrypoint,'runtime/index.html');self.assertIn(m.entrypoint,[x.path for x in m.artifacts])
