import unittest
from bie.game_engine.build_runtime_engine.browser_runtime import browser_smoke
from bie.game_engine.build_runtime_engine.sandbox import canonical_worker_manifest,CANONICAL_BROWSER_WORKER_BLOB,CANONICAL_MAIN
from tests.hardening_h3.support import built
class H3Sandbox(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.td,_,_,cls.ws=built();cls.ev=browser_smoke(cls.ws.root/'dist')
 @classmethod
 def tearDownClass(cls):cls.td.cleanup()
 def test_canonical_worker_identity(self):self.assertEqual(self.ev.canonical_worker_blob,CANONICAL_BROWSER_WORKER_BLOB);self.assertEqual(CANONICAL_MAIN,'375d99af0edd0086206817dae932156ddf61c569')
 def test_worker_contract_tools(self):self.assertEqual(set(canonical_worker_manifest()['tools']),{'node','chromium','playwright'})
 def test_worker_contract_network_deny(self):self.assertEqual(canonical_worker_manifest()['network_default'],'deny')
 def test_worker_contract_sandbox_required(self):self.assertTrue(canonical_worker_manifest()['sandbox'])
 def test_browser_runs_unprivileged(self):self.assertGreater(self.ev.sandbox_uid,0)
 def test_no_new_privileges(self):self.assertTrue(self.ev.sandbox_no_new_privs)
 def test_renderer_seccomp(self):self.assertTrue(self.ev.renderer_seccomp)
 def test_no_external_requests(self):self.assertEqual(self.ev.external_requests,())
 def test_browser_still_studio_grade(self):self.assertTrue(self.ev.studio_grade);self.assertFalse(self.ev.slide_deck)
