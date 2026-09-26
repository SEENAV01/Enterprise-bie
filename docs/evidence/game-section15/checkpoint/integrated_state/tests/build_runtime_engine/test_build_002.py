import unittest
from bie.game_engine.build_runtime_engine.browser_runtime import browser_smoke
from tests.build_runtime_engine.support import built
class Build002(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.td,cls.ctx,cls.assets,cls.ws=built();cls.e=browser_smoke(cls.ws.root/'dist')
 @classmethod
 def tearDownClass(cls):cls.td.cleanup()
 def test_real_browser_boots(self):self.assertTrue(self.e.studio_grade);self.assertFalse(self.e.slide_deck)
 def test_semantic_entities_render(self):self.assertGreaterEqual(self.e.entity_count,2)
 def test_no_external_network(self):self.assertEqual(self.e.external_requests,())
 def test_no_console_errors(self):self.assertEqual(self.e.console_errors,())
 def test_no_page_errors(self):self.assertEqual(self.e.page_errors,())
 def test_all_runtime_programs_bound(self):
  expected={'stateMachine','ruleMetadata','interactionProgram','scoringProgram','feedbackProgram','adaptationMetadata','telemetryProgram','sanitizeTelemetry'};self.assertTrue(expected<=set(self.e.runtime_binding_keys))
 def test_browser_evidence_not_acceptance(self):self.assertFalse(self.e.product_accepted)
