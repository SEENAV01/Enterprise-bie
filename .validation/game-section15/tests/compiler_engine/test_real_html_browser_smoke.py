import unittest,shutil
from bie.game_engine.compiler_engine.html_runtime import compile_html_runtime
from bie.game_engine.compiler_engine.fixtures import compiler_context
class HtmlBrowserSmoke(unittest.TestCase):
 def test_real_chromium_loads_studio_shell(self):
  try:from playwright.sync_api import sync_playwright
  except ImportError:self.skipTest('playwright unavailable')
  chromium=shutil.which('chromium') or shutil.which('chromium-browser');self.assertIsNotNone(chromium)
  html=compile_html_runtime(compiler_context()).content
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path=chromium,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'],timeout=30000)
   try:
    page=b.new_page();page.set_content(html,wait_until='domcontentloaded');root=page.locator('#bie-game-root');self.assertEqual(root.get_attribute('data-studio-grade'),'true');self.assertEqual(root.get_attribute('data-slide-deck'),'false');self.assertEqual(root.get_attribute('role'),'application')
   finally:b.close()
