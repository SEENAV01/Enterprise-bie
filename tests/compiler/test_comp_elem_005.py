import unittest
from bie.compiler.chart_compiler import *
class T(unittest.TestCase):
 def e(self,k="bar"):return {"element_id":"c","element_type":"chart","props":{"chart_kind":k,"categories":["A","B"],"values":[1,2]},"accessibility":{"alt":"chart"},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_bar(self):self.assertIn("baseline",compile_chart_element(self.e()).source_text)
 def test_kind(self):self.assertIn('data-chart-kind={"bar"}',compile_chart_element(self.e()).source_text)
 def test_pie_is_native_without_fallback(self):self.assertEqual(compile_chart_element(self.e("pie")).warnings,())
 def test_bad(self):
  with self.assertRaises(ElementCompilerError):compile_chart_element(self.e("radar"))
 def test_mismatch(self):
  x=self.e();x["props"]["values"]=[1]
  with self.assertRaises(ElementCompilerError):compile_chart_element(x)
