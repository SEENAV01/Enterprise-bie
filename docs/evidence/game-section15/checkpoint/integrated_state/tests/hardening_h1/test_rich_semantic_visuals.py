import unittest,tempfile
from dataclasses import replace
from pathlib import Path
from bie.game_engine.fixtures import sample_document
from bie.game_engine.visual import VisualEntity,VisualKind,VisualExperienceContract
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.build_runtime_engine.fixtures import wav_bytes
from bie.game_engine.compiler_engine.contracts import AssetDescriptor
from bie.game_engine.build_runtime_engine.workspace import build_workspace
from bie.game_engine.build_runtime_engine.toolchain import discover_toolchain
from playwright.sync_api import sync_playwright
import hashlib

class RichSemanticVisualTests(unittest.TestCase):
 def context(self):
  doc=sample_document();exp=doc.experiences[0];level=exp.levels[0];base=list(level.visual.entities);existing={e.kind for e in base}
  for kind in VisualKind:
   if kind in existing:continue
   base.append(VisualEntity('entity:'+kind.value,kind,'semantic_'+kind.value,'source:book',(),kind.value.replace('_',' ')+' semantic visual'))
  visual=VisualExperienceContract(tuple(base),level.visual.motion,level.visual.camera,level.visual.background_role);level=replace(level,visual=visual);exp=replace(exp,levels=(level,));doc=replace(doc,experiences=(exp,))
  ctx=replace(compiler_context(),document=doc);data=wav_bytes();desc=AssetDescriptor('asset:sfx:success','audio/wav',hashlib.sha256(data).hexdigest(),'Success sound').validate();ctx=replace(ctx,assets={'asset:sfx:success':desc});return ctx,{'asset:sfx:success':data}
 def test_all_visual_kinds_render_real_semantic_primitives(self):
  ctx,assets=self.context()
  with tempfile.TemporaryDirectory() as td:
   build_workspace(ctx,assets,Path(td));runtime=Path(td)/'dist/runtime';html=(runtime/'index.html').read_text().replace('<script type="module" src="./entry.js"></script>','');bundle=(runtime/'smoke-bundle.js').read_text();chromium=next(x for x in discover_toolchain()[0] if x.name=='chromium')
   with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=chromium.path,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    try:
     p=b.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.set_content(html);p.evaluate(bundle);p.wait_for_function('globalThis.__BIE_GAME_RUNTIME__?.booted===true');self.assertEqual(p.locator('[data-entity-id]').count(),len(VisualKind));self.assertEqual(p.locator('[data-semantic-svg]').count(),len(VisualKind)-1);kinds=set(p.locator('[data-entity-id]').evaluate_all('(xs)=>xs.map(x=>x.dataset.entityKind)'));self.assertEqual(kinds,{k.value for k in VisualKind});boxes=p.locator('[data-semantic-svg]').evaluate_all('(xs)=>xs.map(x=>{const r=x.getBoundingClientRect();return [r.width,r.height]})');self.assertTrue(all(w>=100 and h>=60 for w,h in boxes));self.assertEqual(errors,[])
    finally:b.close()
