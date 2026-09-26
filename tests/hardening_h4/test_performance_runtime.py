import unittest
from dataclasses import replace
from tests.hardening_h4.support import *
from bie.game_engine.runtime_quality_engine.runtime_audit import verify_runtime_quality
from bie.game_engine.runtime_quality_engine.contracts import PerformanceBudget
from bie.game_engine.errors import GameContractError
class PerformanceRuntimeTests(unittest.TestCase):
 def test_real_browser_runtime_quality(self):
  td,ws=build()
  try:
   e=verify_runtime_quality(ws.root/'dist',profile());self.assertEqual(e.locale,'ur-IN');self.assertEqual(e.direction,'rtl');self.assertTrue(e.keyboard_pass);self.assertTrue(e.touch_targets_pass);self.assertTrue(e.mobile_pass);self.assertTrue(e.tablet_pass);self.assertTrue(e.reduced_motion_pass);self.assertLess(e.interaction_latency_ms,120)
  finally:td.cleanup()
 def test_tight_js_budget_fails(self):
  td,ws=build()
  try:
   p=replace(profile(),performance=replace(profile().performance,max_initial_js_bytes=1));self.assertRaises(GameContractError,verify_runtime_quality,ws.root/'dist',p)
  finally:td.cleanup()
 def test_mobile_budget_validation(self):
  self.assertRaises(GameContractError,PerformanceBudget(mobile_viewport_width=200).validate)
