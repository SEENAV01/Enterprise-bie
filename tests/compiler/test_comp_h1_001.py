import json,unittest
from bie.compiler.text_compiler import compile_text_element
from bie.compiler.annotation_callout_compiler import compile_annotation_callout_element
from bie.compiler.hardening_contracts import literal_child
from bie.compiler.checked_scene_compile import compile_scene_checked
from bie.compiler.generated_code_regression import probe_typescript_sources
from tests.compiler.h1_test_support import element,scene,runtime_tree,text_nodes

class SafeLiteralTests(unittest.TestCase):
    def render(self,text,kind="text"):
        props={"text":text} if kind!="callout" else {"content":text}
        if kind!="text":props["target_element_id"]="anchor"
        result=(compile_text_element if kind=="text" else compile_annotation_callout_element)(element(kind,props))
        return result,runtime_tree(result)
    def test_braces_are_literal(self):self.assertIn('{Math.random()}',text_nodes(self.render('{Math.random()}')[1]))
    def test_script_tags_are_text(self):self.assertIn('<script>alert(1)</script>',text_nodes(self.render('<script>alert(1)</script>')[1]))
    def test_quotes_roundtrip(self):self.assertIn('"single\' and \\ double',text_nodes(self.render('"single\' and \\ double')[1]))
    def test_multilingual_roundtrip(self):self.assertIn('हिन्दी اردو 漢字 😀',text_nodes(self.render('हिन्दी اردو 漢字 😀')[1]))
    def test_whitespace_roundtrip(self):self.assertIn('  a\n\tb  ',text_nodes(self.render('  a\n\tb  ')[1]))
    def test_entities_are_not_double_decoded(self):self.assertIn('&lt; &amp; < >',text_nodes(self.render('&lt; &amp; < >')[1]))
    def test_line_separators(self):self.assertEqual(json.loads(literal_child('a\u2028b\u2029c')[1:-1]),'a\u2028b\u2029c')
    def test_annotation_literal(self):self.assertIn('{Math.random()}',text_nodes(self.render('{Math.random()}','annotation')[1]))
    def test_callout_literal(self):self.assertIn('{Math.random()}',text_nodes(self.render('{Math.random()}','callout')[1]))
    def test_template_string_literal(self):self.assertIn('`${globalThis.x}`',text_nodes(self.render('`${globalThis.x}`')[1]))
    def test_jsx_breakout_remains_literal(self):self.assertIn('</div>{Math.random()}<div>',text_nodes(self.render('</div>{Math.random()}<div>')[1]))
    def test_expression_has_only_one_json_value(self):self.assertEqual(json.loads(literal_child('{1+1}')[1:-1]),'{1+1}')
    def test_unpaired_surrogate_rejected(self):
        with self.assertRaisesRegex(ValueError,'TEXT_VALUE_INVALID'):compile_text_element(element('text',{'text':'\ud800'}))
    def test_oversized_text_rejected(self):
        with self.assertRaises(ValueError):compile_text_element(element('text',{'text':'a'*100001}))
    def test_empty_text_rejected(self):
        with self.assertRaises(ValueError):compile_text_element(element('text',{'text':''}))
    def test_nonstring_rejected(self):
        with self.assertRaises(ValueError):compile_text_element(element('text',{'text':False}))
    def test_invalid_alt_rejected(self):
        with self.assertRaises(ValueError):compile_text_element(element('text',{'text':'x'},alt={'bad':1}))
    def test_source_is_deterministic(self):self.assertEqual(compile_text_element(element('text',{'text':'हिंदी {a}'})),compile_text_element(element('text',{'text':'हिंदी {a}'})))
    def test_newline_style_preserved(self):self.assertIn('whiteSpace: "pre-wrap"',self.render('a')[0].source_text)
    def test_actual_ast_does_not_see_random_call_in_string(self):
        r=compile_text_element(element('text',{'text':'{Math.random()}'}));self.assertEqual(probe_typescript_sources(((r.source_path,r.source_text),)).status,'PASS')
    def test_actual_unsafe_js_is_still_detected(self):
        self.assertIn('QA_UNSEEDED_RANDOM',{f.code for f in probe_typescript_sources((('src/a.ts','const x=Math.random();'),)).findings})
    def test_code_examples_can_pass_checked_source_gate(self):
        _,r=compile_scene_checked(scene('text',{'text':'eval(1); new Function(); animation: x; process.env; document.write()'}));self.assertTrue(r.source_gate_passed)
    def test_no_acceptance_claim(self):self.assertFalse(compile_text_element(element('text',{'text':'ok'})).accepted)

if __name__=='__main__':unittest.main()
