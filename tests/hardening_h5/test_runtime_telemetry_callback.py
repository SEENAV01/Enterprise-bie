import unittest,tempfile
from pathlib import Path
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.build_runtime_engine.workspace import build_workspace
from bie.game_engine.build_runtime_engine.sandbox import sandboxed_chromium
from bie.game_engine.build_runtime_engine.contracts import BuildPolicy
class RuntimeTelemetryCallbackTests(unittest.TestCase):
 def test_real_browser_emits_governed_callback(self):
  ctx,assets=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   ws=build_workspace(ctx,assets,Path(td));runtime=Path(td)/'dist/runtime';html=(runtime/'index.html').read_text().replace('<script type="module" src="./entry.js"></script>','');bundle=(runtime/'smoke-bundle.js').read_text();captured=[]
   with sandboxed_chromium(BuildPolicy()) as (bctx,_,__):
    page=bctx.pages[0] if bctx.pages else bctx.new_page();page.expose_function('captureTelemetry',lambda e:captured.append(e));page.set_content(html);page.evaluate(bundle);page.evaluate("window.__BIE_GAME_TELEMETRY_CONFIG__={enabled:true,policy_id:'policy:telemetry:v1',session_id:'session:browser'};window.__BIE_GAME_TELEMETRY_SINK__=window.captureTelemetry")
    page.locator('[data-entity-id="entity:mover"]').click();page.wait_for_timeout(50)
   events=[x for x in captured if isinstance(x,dict)];self.assertEqual(len(events),1);self.assertEqual(events[0]['event'],'mechanic_completed');self.assertEqual(events[0]['session_id'],'session:browser');self.assertEqual(events[0]['sequence_id'],1);self.assertEqual(events[0]['objective_id'],'obj:motion');self.assertIn('adaptation_id',events[0]);self.assertNotIn('raw_text',events[0])
