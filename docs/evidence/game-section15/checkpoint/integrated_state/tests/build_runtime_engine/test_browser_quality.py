import unittest
from bie.game_engine.build_runtime_engine.browser_runtime import browser_smoke
from tests.build_runtime_engine.support import built
class BrowserQuality(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.td,cls.ctx,cls.assets,cls.ws=built();cls.e=browser_smoke(cls.ws.root/'dist')
 @classmethod
 def tearDownClass(cls):cls.td.cleanup()
 def test_exact_binding_set(self):self.assertEqual(set(self.e.runtime_binding_keys),{'stateMachine','ruleMetadata','interactionProgram','scoringProgram','feedbackProgram','adaptationMetadata','telemetryProgram','sanitizeTelemetry'})
 def test_self_contained_bundle_is_hashed(self):self.assertEqual(len(self.e.bundle_sha256),64)
 def test_execution_mode_is_explicit(self):self.assertEqual(self.e.execution_mode,'playwright_devtools_self_contained_bundle')
 def test_target_does_not_claim_network_origin(self):self.assertEqual(self.e.target,'about:blank')
 def test_studio_not_slides(self):self.assertTrue(self.e.studio_grade);self.assertFalse(self.e.slide_deck)
