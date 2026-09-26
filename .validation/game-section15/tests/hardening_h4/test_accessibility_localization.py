import unittest
from tests.hardening_h4.support import *
from bie.game_engine.compiler_engine.react_runtime import compile_react_runtime
from bie.game_engine.runtime_quality_engine.contracts import *
from bie.game_engine.errors import GameContractError
class AccessibilityLocalizationTests(unittest.TestCase):
 def test_rtl_profile(self):
  p=profile();self.assertEqual(p.catalog().direction,'rtl')
 def test_wrong_direction_fails(self):
  p=LocaleCatalog('ur-IN',{'ui.ready':'x'},'ltr');self.assertRaises(GameContractError,p.validate)
 def test_runtime_has_lang_dir_live_caption_audio(self):
  s=compile_react_runtime(context()).content
  for x in ('ur-IN','rtl','aria-live','data-caption-region','data-audio-control','prefers-reduced-motion'):self.assertIn(x,s)
 def test_keyboard_runtime_present(self):
  from bie.game_engine.compiler_engine.runtime_controller import compile_runtime_controller
  s=compile_runtime_controller(context()).content;self.assertIn('keydown',s);self.assertIn('ArrowRight',s);self.assertIn('Enter',s)
 def test_html_shell_uses_profile_locale_direction(self):
  from bie.game_engine.compiler_engine.html_runtime import compile_html_runtime
  h=compile_html_runtime(context()).content;self.assertIn('lang="ur-IN"',h);self.assertIn('dir="rtl"',h)
 def test_touch_budget_minimum(self):
  self.assertRaises(GameContractError,AccessibilityRuntimePolicy(min_touch_target_px=40).validate)
 def test_catalog_requires_primary(self):
  self.assertRaises(GameContractError,RuntimeExperienceProfile('en-US',(LocaleCatalog('ur-IN',{'ui.ready':'x'},'rtl'),)).validate)
