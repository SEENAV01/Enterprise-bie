"""Real browser diagnostic integration. Never actual React/Remotion acceptance."""
import json, tempfile, unittest, shutil
from pathlib import Path
from dataclasses import replace
from copy import deepcopy
from bie.compiler.hardened_scene_compile import compile_h3_scene, publish_h3_scene,require_h3_workspace
from bie.compiler.raster_browser import measure_raster_scene
from bie.compiler.raster_capture import DIAGNOSTIC_SCOPE,required_paint
from bie.compiler.real_paint import require_actual_witness
from tests.compiler.h8_test_support import *
from tests.compiler.h6_test_support import state_scene,narration_scene,BIG
SUPPORT=Path(__file__).parents[2]/'app/bie/compiler/qa_support'

class BrowserIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name);cls.results={}
        for name,p in [('text',raw_text()),('map',map_scene()),('overlap',map_scene(overlap=True)),('tiny',map_scene(tiny_polygon=True))]:
            c=compile_h3_scene(p,target=BROWSER)
            cls.results[name]=measure_raster_scene(c,BROWSER,cls.root/name)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_real_browser_text_all_frames(self):r=self.results['text'];self.assertTrue(r['passed']);self.assertEqual(r['frame_count'],2);self.assertEqual(r['image_count'],10)
    def test_real_projected_points_preserved(self):self.assertTrue(self.results['map']['passed']);self.assertEqual(self.results['map']['target_frame_records'],6)
    def test_collocated_markers_not_hidden_by_owner_bbox(self):r=self.results['overlap'];self.assertFalse(r['passed']);self.assertIn('MAP_POINTS_VISUALLY_UNRESOLVED',{f['code'] for f in r['findings']})
    def test_subpixel_polygon_detected(self):r=self.results['tiny'];self.assertFalse(r['passed']);self.assertIn('MAP_POLYGON_COLLAPSED',{f['code'] for f in r['findings']})
    def test_diagnostics_cannot_mint_witness(self):self.assertRaises(ValueError,require_actual_witness,self.results['text'],'a'*64)
    def test_no_network_requests(self):r=json.loads((self.root/'map/PRODUCER.json').read_text());self.assertEqual(r['network_denied'],[]);self.assertFalse(r['real_remotion']);self.assertFalse(r['real_react'])
    def test_every_mode_has_bound_hashed_png(self):r=json.loads((self.root/'map/CAPTURE.json').read_text());self.assertEqual(r['scope'],DIAGNOSTIC_SCOPE);self.assertEqual(len(list((self.root/'map').glob('*.png'))),22)
    def test_existing_output_not_overwritten(self):c=compile_h3_scene(raw_text(),target=BROWSER);self.assertRaisesRegex(ValueError,'OUTPUT_EXISTS',measure_raster_scene,c,BROWSER,self.root/'text')
    def test_dynamic_intent_observed_from_source(self):
        p=state_scene();early=required_paint(p,BIG,0);late=required_paint(p,BIG,47);self.assertIn('e0',early);self.assertIn('e0',late)
    def test_original_source_checks_still_roundtrip(self):
        p=raw_text();root=self.root/'publish';receipt=publish_h3_scene(p,root,target=BROWSER);self.assertEqual(receipt,require_h3_workspace(root))

class ReversibleBrowserModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);cls.page=cls.browser.new_page(viewport={'width':160,'height':120});cls.helper=(SUPPORT/'raster_modes.js').read_text()
    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.pw.stop()
    def setUp(self):
        self.page.set_content('<div data-bie-layer-id="a"><svg width="120" height="90"><g><circle data-layer-id="p" cx="10" cy="10" r="4" style="visibility:visible!important"/><circle data-layer-id="q" cx="50" cy="50" r="4"/></g></svg></div><div data-bie-layer-id="b">Cover</div>')
        self.ts=[{'target_id':'owner:0','element_id':'a','layer_id':None},{'target_id':'map:0:0','element_id':'a','layer_id':'p'},{'target_id':'owner:1','element_id':'b','layer_id':None}]
    def call(self,kind='full',tid=None):return self.page.evaluate(self.helper,{'targets':self.ts,'mode':{'kind':kind,**({'target_id':tid} if tid else {})},'frame':0})
    def test_inline_important_visibility_hidden_and_restored(self):
        self.call('muted','owner:0');self.assertEqual(self.page.locator('[data-layer-id=p]').evaluate('(e)=>getComputedStyle(e).visibility'),'hidden');self.call();self.assertEqual(self.page.locator('[data-layer-id=p]').evaluate('(e)=>e.style.getPropertyPriority("visibility")'),'important');self.assertEqual(self.page.locator('[data-layer-id=p]').evaluate('(e)=>getComputedStyle(e).visibility'),'visible')
    def test_isolated_feature_hides_sibling_only(self):
        self.call('isolated','map:0:0');self.assertEqual(self.page.locator('[data-layer-id=p]').evaluate('(e)=>getComputedStyle(e).visibility'),'visible');self.assertEqual(self.page.locator('[data-layer-id=q]').evaluate('(e)=>getComputedStyle(e).visibility'),'hidden')
    def test_modes_preserve_text_and_coordinates(self):
        before=self.page.locator('body').inner_text();self.call('baseline','map:0:0');self.call();self.assertEqual(before,self.page.locator('body').inner_text());self.assertEqual(self.page.locator('[data-layer-id=p]').get_attribute('cx'),'10')
    def test_new_mode_restores_before_collecting_inventory(self):
        a=self.call();self.call('muted','owner:0');b=self.call('isolated','map:0:0');self.assertEqual(a['inventory'],b['inventory'])
    def test_unknown_owner_rejected(self):
        self.page.evaluate('()=>{const d=document.createElement("div");d.dataset.bieLayerId="unknown";document.body.append(d)}')
        with self.assertRaisesRegex(Exception,'UNDECLARED_OWNER'):self.call()
    def test_duplicate_owner_rejected(self):self.page.evaluate('()=>{document.body.append(document.querySelector("div").cloneNode(true))}');self.assertRaises(Exception,self.call)
    def test_unsupported_blending_recorded(self):self.page.locator('[data-layer-id=p]').evaluate('(e)=>e.style.mixBlendMode="multiply"');self.assertTrue(self.call()['inventory'][1]['unresolved_effect'])
    def test_target_id_not_css_selector_interpolation(self):self.ts[1]['layer_id']='p]circle';self.assertRaises(Exception,self.call)
