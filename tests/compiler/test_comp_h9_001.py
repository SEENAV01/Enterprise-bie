import unittest
from copy import deepcopy
from hashlib import sha256
from bie.compiler.shape_compiler import *
from tests.compiler.h9_test_support import shape_scene,runtime,nodes
from bie.compiler.generated_code_regression import probe_typescript_sources

class ShapeConsumerTests(unittest.TestCase):
    def element(self,kind='rectangle'):return shape_scene(kind)['elements'][0]
    def bad(self,e,code):
        with self.assertRaisesRegex(ValueError,code):compile_shape_element(e)
    def test_all_original_kinds_have_actual_geometry(self):
        for k in sorted(KINDS):
            with self.subTest(k=k):
                r=compile_shape_element(self.element(k));out=runtime(r);tags=[n['tag'] for n in nodes(out['trees'][0]['tree'])]
                self.assertIn({'rectangle':'rect','arrow':'line'}.get(k,k),tags)
    def test_arrowhead_has_direction_and_is_not_plain_line(self):
        g=shape_geometry(self.element('arrow')['props']);self.assertEqual(g['arrowhead'][1],[80,70]);self.assertLess(g['arrowhead'][0][0],80)
    def test_open_polyline_has_no_closing_segment(self):
        r=compile_shape_element(self.element('polyline'));self.assertIn('"tag": "polyline"',r.source_text)
    def test_geometry_not_mutated(self):
        e=self.element();before=deepcopy(e);compile_shape_element(e);self.assertEqual(e,before)
    def test_repeatable_bytes_and_hash(self):
        r=compile_shape_element(self.element());self.assertEqual(r,compile_shape_element(self.element()));self.assertEqual(r.source_sha256,sha256(r.source_text.encode()).hexdigest())
    def test_negative_dimensions(self):
        e=self.element();e['props']['geometry']['width']=-1;self.bad(e,'BOUNDS')
    def test_nan_geometry(self):
        e=self.element();e['props']['geometry']['x']=float('nan');self.bad(e,'NUMERIC')
    def test_bool_geometry(self):
        e=self.element();e['props']['geometry']['x']=True;self.bad(e,'NUMERIC')
    def test_extra_required_property_not_ignored(self):
        e=self.element();e['props']['extrude']=1;self.bad(e,'FIELDS')
    def test_extra_geometry_not_ignored(self):
        e=self.element();e['props']['geometry']['z']=2;self.bad(e,'FIELDS')
    def test_viewbox_required(self):
        e=self.element();del e['props']['geometry']['view_box'];self.bad(e,'FIELDS')
    def test_stroke_clipping_rejected(self):
        e=self.element();e['props']['geometry']['x']=0;self.bad(e,'OUTSIDE')
    def test_stroke_url_rejected(self):
        e=self.element();e['props']['style']['stroke']='url(https://bad)';self.bad(e,'UNSAFE')
    def test_opacity_zero_rejected(self):
        e=self.element();e['props']['style']['opacity']=0;self.bad(e,'INVISIBLE')
    def test_empty_paint_rejected(self):
        e=self.element();e['props']['style']['stroke']='none';self.bad(e,'INVISIBLE')
    def test_zero_length_line_rejected(self):
        e=self.element('line');e['props']['geometry'].update(x2=20,y2=20);self.bad(e,'DEGENERATE')
    def test_self_intersecting_polygon_rejected(self):
        e=self.element('polygon');e['props']['geometry']['points']=[[10,10],[90,90],[10,90],[90,10]];self.bad(e,'INTERSECTION')
    def test_closed_polygon_canonicalized_without_lost_vertex(self):
        e=self.element('polygon');e['props']['geometry']['points'].append([20,20]);g=shape_geometry(e['props']);self.assertEqual(len(g['attrs']['points'].split()),4)
    def test_adjacent_duplicate_rejected(self):
        e=self.element('polyline');e['props']['geometry']['points']=[[10,10],[10,10]];self.bad(e,'DEGENERATE')
    def test_alt_required(self):
        e=self.element();e['accessibility']={};self.bad(e,'TEXT')
    def test_literal_alt_not_executable(self):
        e=self.element();e['accessibility']['alt']='{globalThis.BAD=true} <script> नमस्ते';r=compile_shape_element(e);out=runtime(r);self.assertIn(e['accessibility']['alt'],str(out))
    def test_real_typescript_parser(self):
        r=compile_shape_element(self.element());self.assertEqual(probe_typescript_sources([(r.source_path,r.source_text)]).status,'PASS')
    def test_source_lineage_required(self):
        e=self.element();e['source_refs']=[];self.bad(e,'lineage')
    def test_no_product_acceptance_claim(self):self.assertFalse(compile_shape_element(self.element()).accepted)

    def test_invalid_five_digit_hex_color_rejected(self):
        e=self.element();e['props']['style']['stroke']='#12345';self.bad(e,'UNSAFE')
    def test_hidden_alpha_is_not_a_backdoor_to_invisible_required_geometry(self):
        e=self.element();e['props']['style']['stroke']='#12345600';self.bad(e,'UNSAFE')
