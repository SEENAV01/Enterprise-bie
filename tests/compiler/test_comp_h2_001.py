from copy import deepcopy
from hashlib import sha256
from unittest.mock import patch
import json,re,unittest
from bie.compiler.equation_compiler import compile_equation_element
from bie.compiler.equation_typesetting import typeset_latex,mathml_tree,_latex_cached
from bie.compiler.generated_code_regression import probe_typescript_sources
from tests.compiler.h2_test_support import element,runtime,nodes,text_nodes

class EquationTypesettingTests(unittest.TestCase):
    def compile(self,expr='x^2',fmt='latex',**kw):
        return compile_equation_element(element('equation',{'expression':expr,'format':fmt,**kw}))
    def test_real_fraction_has_glyph_paths(self):
        r=self.compile(r'\frac{x^2}{\sqrt{y}}');t=runtime(r)['trees'][0]['tree'];self.assertGreater(len(nodes(t,'path')),3);self.assertGreater(len(nodes(t,'use')),2)
    def test_supported_commands_not_rendered_as_raw_text(self):
        r=self.compile(r'\frac{1}{2}');self.assertNotIn('{expression}',r.source_text);self.assertNotIn(r'\frac', ''.join(text_nodes(runtime(r)['trees'][0]['tree'])))
    def test_square_root_layout_is_nonempty(self):
        x=typeset_latex(r'\sqrt{x}',element_id='q');self.assertGreater(x['view_box'][2],0);self.assertGreater(x['view_box'][3],0)
    def test_subscript_superscript_typeset(self):self.assertIn('tree',typeset_latex(r'a_i^2',element_id='q'))
    def test_sum_and_integral_supported(self):
        for s in (r'\sum_{i=1}^{n} i',r'\int_0^1 x\,dx'):self.assertGreater(len(typeset_latex(s,element_id='q')['tree']['children']),0)
    def test_used_font_hashes_not_font_files(self):
        d=typeset_latex('x^2',element_id='q');self.assertTrue(d['font_hashes']);self.assertTrue(all(len(h)==64 for h in d['font_hashes'].values()));self.assertNotIn('font_base64',d)
    def test_backend_version_pinned(self):self.assertEqual(typeset_latex('x',element_id='q')['matplotlib_version'],'3.10.8')
    def test_typesetter_unavailable_fails_closed(self):
        _latex_cached.cache_clear()
        with patch.dict('sys.modules',{'matplotlib':None}):
            with self.assertRaisesRegex(ValueError,'UNAVAILABLE'):typeset_latex('q+12345',element_id='missing')
    def test_wrong_backend_version_blocked(self):
        import matplotlib
        _latex_cached.cache_clear()
        with patch.object(matplotlib,'__version__','0.0.0'):
            with self.assertRaisesRegex(ValueError,'VERSION_MISMATCH'):typeset_latex('q+98765',element_id='wrong')
    def test_typesetting_bytes_repeatable_without_cache(self):
        _latex_cached.cache_clear();a=self.compile(r'\frac{x}{y}');_latex_cached.cache_clear();b=self.compile(r'\frac{x}{y}');self.assertEqual(a,b)
    def test_glyph_ids_isolated_by_element(self):
        a=typeset_latex('x',element_id='a')['tree'];b=typeset_latex('x',element_id='b')['tree'];self.assertNotEqual(a,b)
    def test_cached_return_cannot_be_mutated(self):
        a=typeset_latex('x',element_id='a');a['tree']['children']=[];self.assertTrue(typeset_latex('x',element_id='a')['tree']['children'])
    def test_no_clock_metadata_in_emitted_layout(self):
        s=self.compile().source_text;self.assertNotIn('dc:date',s);self.assertNotIn('2026-',s)
    def test_no_dynamic_html_escape_hatch(self):self.assertNotIn('dangerouslySetInnerHTML',self.compile().source_text)
    def test_unsupported_latex_not_raw_fallback(self):
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED'):self.compile(r'\notARealMacro{x}')
    def test_external_latex_blocked(self):
        for s in (r'\input{/etc/passwd}',r'\href{https://example.com}{x}',r'\includegraphics{bad}'):
            with self.assertRaisesRegex(ValueError,'UNSAFE'):self.compile(s)
    def test_delimiter_injection_rejected(self):
        with self.assertRaises(ValueError):self.compile('$x$')
    def test_newline_latex_rejected(self):
        with self.assertRaises(ValueError):self.compile('x\ny')
    def test_excessive_grouping_rejected(self):
        with self.assertRaisesRegex(ValueError,'COMPLEXITY'):self.compile('{'*25+'x'+'}'*25)
    def test_unbalanced_group_rejected(self):
        with self.assertRaises(ValueError):self.compile(r'\frac{x}{y')
    def test_font_bounds_rejected(self):
        for v in (True,0,1000,32.5):
            with self.assertRaises(ValueError):self.compile(font_size=v)
    def test_plain_text_braces_remain_text(self):
        text='{Math.random()} <script> & Hindi हिंदी';t=runtime(self.compile(text,'plain'))['trees'][0]['tree'];self.assertIn(text,text_nodes(t))
    def test_plain_does_not_advertise_typesetter(self):self.assertEqual(self.compile('x','plain').warnings,())
    def test_side_conditions_preserved(self):
        t=runtime(self.compile(side_conditions=['x > 0','y ≠ 0']))['trees'][0]['tree'];self.assertIn('x > 0, y ≠ 0',text_nodes(t))
    def test_side_condition_wrong_type_rejected(self):
        with self.assertRaises(ValueError):self.compile(side_conditions=[{'x':1}])
    def test_unknown_properties_not_dropped(self):
        with self.assertRaises(ValueError):self.compile(color='red')
    def test_unknown_renderer_not_substituted(self):
        with self.assertRaises(ValueError):self.compile(renderer='anything')
    def test_native_mathml_tree_emitted(self):
        t=runtime(self.compile('<math><mfrac><mi>x</mi><mn>2</mn></mfrac></math>','mathml'))['trees'][0]['tree'];self.assertEqual(len(nodes(t,'mfrac')),1)
    def test_mathml_entities_decode_as_literal_tokens(self):
        d=mathml_tree('<math><mtext>&lt;script&gt;</mtext></math>');self.assertEqual(d['tree']['children'][0]['children'],['<script>'])
    def test_mathml_script_and_event_attribute_blocked(self):
        for s in ('<math><script>x</script></math>','<math onclick="x"><mi>x</mi></math>'):
            with self.assertRaisesRegex(ValueError,'UNSAFE'):mathml_tree(s)
    def test_mathml_doctype_entities_blocked(self):
        with self.assertRaisesRegex(ValueError,'UNSAFE'):mathml_tree('<!DOCTYPE math [<!ENTITY x SYSTEM "file:///x">]><math><mi>&x;</mi></math>')
    def test_mathml_wrong_namespace_blocked(self):
        with self.assertRaises(ValueError):mathml_tree('<math xmlns="http://bad/"><mi>x</mi></math>')
    def test_mathml_fraction_arity_checked(self):
        with self.assertRaisesRegex(ValueError,'ARITY'):mathml_tree('<math><mfrac><mi>x</mi></mfrac></math>')
    def test_mathml_naked_text_not_silently_reinterpreted(self):
        with self.assertRaises(ValueError):mathml_tree('<math>x+y</math>')
    def test_mathml_unsupported_attribute_not_ignored(self):
        with self.assertRaises(ValueError):mathml_tree('<math><mi href="https://bad">x</mi></math>')
    def test_generated_typescript_ast_passes(self):
        r=self.compile();self.assertEqual(probe_typescript_sources(((r.source_path,r.source_text),)).status,'PASS')
    def test_compiler_receipt_not_acceptance(self):self.assertFalse(self.compile().accepted)

    def test_mathtext_viewbox_has_explicit_ink_safety_padding(self):
        layout=typeset_latex(r'\frac{x^2+1}{\sqrt{y}}',element_id='pad')
        self.assertLess(layout['view_box'][0],0);self.assertLess(layout['view_box'][1],0)
        self.assertEqual(len(layout['tree']['attrs']['viewBox'].split()),4)

if __name__=='__main__':unittest.main()
