import unittest,tempfile
from pathlib import Path
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.build_runtime_engine.workspace import build_workspace
from bie.game_engine.build_runtime_engine.toolchain import discover_toolchain
from playwright.sync_api import sync_playwright
class RealBrowserGameplayTests(unittest.TestCase):
 def test_real_browser_nonblank_geometry_and_live_dispatch(self):
  ctx,assets=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   ws=build_workspace(ctx,assets,Path(td));dist=Path(td)/'dist/runtime';html=(dist/'index.html').read_text().replace('<script type="module" src="./entry.js"></script>','');bundle=(dist/'smoke-bundle.js').read_text();chromium=next(x for x in discover_toolchain()[0] if x.name=='chromium')
   with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=chromium.path,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'],timeout=30000)
    try:
     page=browser.new_page();console=[];errors=[];page.on('console',lambda m:console.append(m.text) if m.type=='error' else None);page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(html,wait_until='load');page.evaluate(bundle);page.wait_for_function('globalThis.__BIE_GAME_RUNTIME__?.booted===true')
     body=page.locator('body').inner_text().strip();geom=page.evaluate('() => Array.from(document.querySelectorAll("[data-entity-id]")).map(n=>{const r=n.getBoundingClientRect();return {id:n.dataset.entityId,w:r.width,h:r.height,text:(n.textContent||"").trim()}})');self.assertTrue(body);self.assertTrue(geom);self.assertTrue(all(x['w']>8 and x['h']>8 and x['text'] for x in geom));self.assertEqual(console,[]);self.assertEqual(errors,[])
     before=page.evaluate('globalThis.__BIE_GAME_RUNTIME__.getState()');result=page.evaluate('globalThis.__BIE_GAME_RUNTIME__.dispatch("drag:mover", {x:2,y:0})');after=page.evaluate('globalThis.__BIE_GAME_RUNTIME__.getState()');self.assertTrue(result['applied']);self.assertEqual(before['x'],1);self.assertEqual(after['x'],2);self.assertGreater(page.evaluate('globalThis.__BIE_GAME_RUNTIME__.getScore()'),0);self.assertIn('Correct',page.evaluate('globalThis.__BIE_GAME_RUNTIME__.getFeedback()'));self.assertGreaterEqual(len(page.evaluate('globalThis.__BIE_GAME_RUNTIME__.getTelemetry()')),1);self.assertEqual(page.locator('[data-motion-kind]').count(),1);self.assertEqual(page.locator('main[role="application"]').get_attribute('data-camera-kind'),'focus')
    finally:browser.close()
