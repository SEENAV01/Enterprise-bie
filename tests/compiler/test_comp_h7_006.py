import math,unittest
from copy import deepcopy
from pathlib import Path
from playwright.sync_api import sync_playwright
from bie.compiler.paint_quality import inspect_paint_quality

def sample():return [{'element_id':'e0','frame':0,'text':[{'text_id':'e0:node:0','text':'Visible','font_ready':True,'contrast':21.,'boxes':[{'box':[10,10,100,20],'tested_points':3,'occluded_points':0,'ancestor_clip':False}]}]}]
def check(r):return inspect_paint_quality(r,element_ids=['e0'],frame_count=1)
class PaintContractTests(unittest.TestCase):
    def test_positive(self):self.assertTrue(check(sample())['passed'])
    def test_no_acceptance(self):self.assertFalse(check(sample())['accepted'])
    def test_low_contrast(self):r=sample();r[0]['text'][0]['contrast']=2;self.assertIn('PAINT_TEXT_LOW_CONTRAST',str(check(r)))
    def test_unresolved_contrast_blocks(self):r=sample();r[0]['text'][0]['contrast']=None;self.assertFalse(check(r)['passed'])
    def test_occluded(self):r=sample();r[0]['text'][0]['boxes'][0]['occluded_points']=1;self.assertFalse(check(r)['passed'])
    def test_clipped(self):r=sample();r[0]['text'][0]['boxes'][0]['ancestor_clip']=True;self.assertFalse(check(r)['passed'])
    def test_missing_font(self):r=sample();r[0]['text'][0]['font_ready']=False;self.assertFalse(check(r)['passed'])
    def test_no_box(self):r=sample();r[0]['text'][0]['boxes']=[];self.assertFalse(check(r)['passed'])
    def test_missing_frame(self):
        with self.assertRaisesRegex(ValueError,'COVERAGE'):inspect_paint_quality(sample(),element_ids=['e0'],frame_count=2)
    def test_duplicate_frame(self):
        with self.assertRaisesRegex(ValueError,'IDENTITY'):inspect_paint_quality(sample()*2,element_ids=['e0'],frame_count=2)
    def test_duplicate_text(self):r=sample();r[0]['text']*=2;self.assertRaises(ValueError,check,r)
    def test_nan_contrast(self):r=sample();r[0]['text'][0]['contrast']=math.nan;self.assertRaises(ValueError,check,r)
    def test_nan_box(self):r=sample();r[0]['text'][0]['boxes'][0]['box'][0]=math.nan;self.assertRaises(ValueError,check,r)
    def test_bool_frame(self):r=sample();r[0]['frame']=False;self.assertRaises(ValueError,check,r)
    def test_invalid_ids(self):self.assertRaises(ValueError,inspect_paint_quality,sample(),element_ids=['e0','e0'],frame_count=1)
    def test_sampling_budget_fail_closed(self):self.assertRaisesRegex(ValueError,'BUDGET',inspect_paint_quality,[],element_ids=['e0'],frame_count=2401)
    def test_malformed_object(self):r=sample();r[0]['text']=[None];self.assertRaises(ValueError,check,r)

class ActualChromiumPaintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'],headless=True)
        cls.js=(Path(__file__).parents[2]/'bie/compiler/qa_support/paint_measure.js').read_text()
    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.pw.stop()
    def measure(self,style='',overlay='',text='Visible math and हिंदी اردو'):
        p=self.browser.new_page(viewport={'width':640,'height':360});p.set_content(f'<style>body{{background:white;color:black;font:24px sans-serif}}#e{{position:absolute;top:20px;left:20px;width:400px;height:80px;{style}}}</style><div id="e" data-bie-layer-id="e0">{text}</div>'+overlay)
        p.evaluate('document.fonts.ready');r=p.evaluate(self.js,{'frame':0});p.close();return check(r)
    def test_real_browser_normal(self):self.assertTrue(self.measure()['passed'])
    def test_real_browser_low_contrast(self):self.assertIn('PAINT_TEXT_LOW_CONTRAST',str(self.measure('color:#eee;')))
    def test_real_browser_occlusion(self):self.assertIn('PAINT_TEXT_OCCLUDED',str(self.measure(overlay='<div style="position:absolute;z-index:2;left:0;top:0;width:640px;height:100px;background:white"></div>')))
    def test_real_browser_clip(self):self.assertIn('PAINT_ANCESTOR_CLIPPING',str(self.measure(text='<span style="display:block;width:20px;overflow:hidden">Reallylongliteraltext</span>')))
    def test_real_browser_unresolved_gradient(self):self.assertIn('PAINT_CONTRAST_UNRESOLVED',str(self.measure('background:linear-gradient(white,black);')))
    def test_real_browser_vector_clipping(self):self.assertIn('PAINT_VECTOR_INK_CLIPPED',str(self.measure(text='<svg width="100" height="60" style="overflow:hidden"><circle cx="95" cy="30" r="25" fill="black"/></svg>')))
    def test_real_browser_vector_ink_fits(self):self.assertTrue(self.measure(text='<svg width="100" height="60"><circle cx="40" cy="30" r="20" fill="black"/></svg>')['passed'])
    def test_real_browser_transparent_wrapper_is_not_ink(self):self.assertTrue(self.measure(overlay='<div style="position:absolute;z-index:2;inset:0;pointer-events:none"></div>')['passed'])
    def test_real_browser_pointer_none_opaque_overlay_detected(self):self.assertIn('PAINT_TEXT_OCCLUDED',str(self.measure(overlay='<div style="position:absolute;z-index:2;inset:0;background:white;pointer-events:none"></div>')))
    def test_real_browser_transparency(self):self.assertIn('PAINT_TEXT_LOW_CONTRAST',str(self.measure('opacity:.1;')))

class InstalledFontCoverageTests(unittest.TestCase):
    def test_latin_greek_actual_fonts(self):
        from bie.compiler.font_coverage import system_font_coverage
        r=system_font_coverage(['English αβγ']);self.assertTrue(r['passed']);self.assertTrue(r['font_identities']);self.assertFalse(r['accepted'])
    def test_devanagari_actual_fonts(self):
        from bie.compiler.font_coverage import system_font_coverage
        self.assertTrue(system_font_coverage(['हिंदी गणित'])['passed'])
    def test_arabic_urdu_actual_fonts(self):
        from bie.compiler.font_coverage import system_font_coverage
        self.assertTrue(system_font_coverage(['اردو العربية'])['passed'])
    def test_cjk_actual_fonts(self):
        from bie.compiler.font_coverage import system_font_coverage
        self.assertTrue(system_font_coverage(['中文'])['passed'])
    def test_unavailable_private_glyph_not_guessed(self):
        from bie.compiler.font_coverage import system_font_coverage
        self.assertFalse(system_font_coverage(['\U0010ffff'])['passed'])
    def test_glyph_budget_no_sampling(self):
        from bie.compiler.font_coverage import system_font_coverage
        self.assertRaisesRegex(ValueError,'BUDGET',system_font_coverage,['abc'],max_codepoints=2)
    def test_unsafe_family_reject(self):
        from bie.compiler.font_coverage import system_font_coverage
        self.assertRaises(ValueError,system_font_coverage,['a'],family='file=/etc/passwd')
    def test_font_bytes_not_embedded(self):
        from bie.compiler.font_coverage import system_font_coverage
        r=system_font_coverage(['a']);self.assertTrue(all(set(x)=={'sha256','bytes','basename','face_index'} for x in r['font_identities']))
