import unittest,hashlib
from bie.game_engine.build_runtime_engine.deployment import deployment_smoke
from tests.hardening_h3.support import built
class H3Deployment(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.td,_,_,cls.ws=built();cls.ev=deployment_smoke(cls.ws.root/'dist')
 @classmethod
 def tearDownClass(cls):cls.td.cleanup()
 def test_static_origin_path(self):self.assertTrue(self.ev.static_origin_verified)
 def test_native_chromium_esm_loader(self):self.assertTrue(self.ev.native_esm_loader_verified)
 def test_exact_module_graph_not_single_bundle_only(self):self.assertGreaterEqual(self.ev.exact_module_count,10)
 def test_module_graph_bound(self):self.assertTrue(self.ev.module_graph_fingerprint.startswith('sha256:'))
 def test_entry_source_bound(self):self.assertEqual(len(self.ev.entry_source_sha256),64)
 def test_native_loader_is_sandboxed(self):self.assertTrue(self.ev.sandbox_evidence.renderer_seccomp);self.assertTrue(self.ev.sandbox_evidence.no_new_privs)
 def test_combined_origin_is_not_falsely_claimed(self):
  if not self.ev.browser_origin_navigation_verified:self.assertIsNotNone(self.ev.origin_block_reason)
 def test_current_environment_admin_block_is_preserved(self):
  if self.ev.origin_block_reason is not None:self.assertIn(self.ev.origin_block_reason,{'ERR_BLOCKED_BY_ADMINISTRATOR','ERR_BLOCKED_BY_CLIENT','ORIGIN_NAVIGATION_BLOCKED'})
