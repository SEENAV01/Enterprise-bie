from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import json,subprocess,tempfile,unittest
from bie.compiler.text_compiler import compile_text_element
from bie.compiler.map_compiler import compile_map_element
from bie.compiler.layout_repair_contracts import candidates
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.generated_code_regression import probe_typescript_sources
from tests.compiler.h4_test_support import text_case,map_case,TARGET_BIG
from tests.compiler.h2_test_support import runtime,nodes

class ReflowEmitterTests(unittest.TestCase):
    def text(self,content=None):
        p,q=text_case(content);return list(candidates(p,q))[1].document['elements'][0]
    def map(self):
        p,q=map_case();return list(candidates(p,q))[1].document['elements'][0]
    def test_text_has_actual_wrap_styles(self):
        s=compile_text_element(self.text()).source_text;self.assertIn('"overflowWrap": "anywhere"',s);self.assertIn('"whiteSpace": "pre-wrap"',s)
    def test_no_ellipsis_or_clipping(self):
        for s in [compile_text_element(self.text()).source_text,compile_map_element(self.map()).source_text]:
            self.assertNotIn('ellipsis',s);self.assertNotIn('overflow: "hidden"',s);self.assertNotIn('lineClamp',s)
    def test_text_font_is_explicit_not_auto_shrunk(self):self.assertIn('"fontSize": 16.0',compile_text_element(self.text()).source_text)
    def test_text_bidi_is_explicit(self):self.assertIn('dir="auto"',compile_text_element(self.text()).source_text)
    def test_empty_text_not_repaired_to_fake_content(self):
        e=self.text();e['props']['text']=''
        with self.assertRaises(ValueError):compile_text_element(e)
    def test_text_literal_injection_stays_escaped(self):
        s=compile_text_element(self.text('{process.exit(1)} <script>literal</script>')).source_text
        self.assertNotIn('<script>literal',s);self.assertIn('\\u003cscript',s)
    def test_unicode_and_newlines_preserved_in_runtime_literal(self):
        e=self.text('क्षेत्र\nاردو\nArea = 2 m²');s=compile_text_element(e).source_text
        self.assertIn('\\u0915',s);self.assertIn('\\n',s)
    def test_unknown_text_property_rejected_in_new_contract(self):
        e=self.text();e['props']['truncate']=True
        with self.assertRaisesRegex(ValueError,'UNCONSUMED'):compile_text_element(e)
    def test_invalid_text_css_rejected(self):
        e=self.text();e['props']['compiler_layout']['font_px']='16px'
        with self.assertRaises(ValueError):compile_text_element(e)
    def test_map_legend_is_responsive_grid(self):
        s=compile_map_element(self.map()).source_text;self.assertIn('gridTemplateColumns',s);self.assertIn('<li',s);self.assertNotIn('(i%3)*310',s)
    def test_map_projection_coordinates_preserved(self):
        s=compile_map_element(self.map()).source_text;self.assertIn('source_points',s);self.assertIn('projected_points',s);self.assertIn('web_mercator',s)
    def test_map_attribution_and_limit_preserved(self):
        s=compile_map_element(self.map()).source_text;self.assertIn('geometry.attribution',s);self.assertIn('not geodesic paths or distance/area',s)
    def test_map_every_label_is_present(self):
        s=compile_map_element(self.map()).source_text;self.assertIn('W'*76,s);self.assertIn('geometry.layers.map',s)
    def test_map_plot_height_is_not_invented_data(self):
        e=self.map();e['props']['compiler_layout']['plot_height_px']=200
        self.assertIn('height={200.0}',compile_map_element(e).source_text)
    def test_map_columns_are_bounded(self):
        e=self.map();e['props']['compiler_layout']['legend_columns']=0
        with self.assertRaises(ValueError):compile_map_element(e)
    def test_map_unknown_semantic_prop_still_blocked(self):
        e=self.map();e['props']['fake_scale']=10
        with self.assertRaisesRegex(ValueError,'UNCONSUMED'):compile_map_element(e)
    def test_map_missing_projection_still_rejected(self):
        e=self.map();e['props'].pop('projection')
        with self.assertRaisesRegex(ValueError,'PROJECTION_REQUIRED'):compile_map_element(e)
    def test_new_emission_is_byte_deterministic(self):
        self.assertEqual(compile_map_element(self.map()),compile_map_element(self.map()))
    def test_legacy_text_has_no_new_layout_marker(self):
        p,_=text_case();self.assertNotIn('data-bie-text-id',compile_text_element(p['elements'][0]).source_text)
    def test_legacy_map_still_retains_historical_source(self):
        p,_=map_case();self.assertIn('(i%3)*310',compile_map_element(p['elements'][0]).source_text)
    def test_new_emitter_source_gate_and_real_parser(self):
        for p,q in [text_case(),map_case()]:
            c=list(candidates(p,q))[1];r=compile_h3_scene(c.document,target=TARGET_BIG);self.assertTrue(r.receipt.source_gate_passed);self.assertEqual(r.receipt.parser_status,'PASS')
    def test_new_emitters_strict_tsc_with_explicit_declaration_doubles(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for i,r in enumerate([compile_text_element(self.text()),compile_map_element(self.map())]):(root/f'c{i}.tsx').write_text(r.source_text)
            (root/'ambient.d.ts').write_text("""declare module 'react' { namespace React { type FC<P={}>=(p:P)=>unknown; } export = React; }
declare module 'react/jsx-runtime' { export namespace JSX { interface IntrinsicElements {[name:string]:any;} } }
declare module 'remotion' { export const Interactive: {Div: (props:any)=>any}; }
""")
            run=subprocess.run(['tsc','--noEmit','--strict','--esModuleInterop','--moduleResolution','node','--target','ES2022','--jsx','react-jsx',*map(str,root.glob('*'))],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)

if __name__=='__main__':unittest.main()
