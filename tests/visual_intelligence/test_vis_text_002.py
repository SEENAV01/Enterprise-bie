import unittest
from bie.visual_intelligence.text_contracts import *
from bie.visual_intelligence.equation_typography import *
def i(text="E=mc^2"):return TextIntent("eq",text,"equation",("e",),("r",))
class T(unittest.TestCase):
 def test_typeset(self):self.assertEqual(equation_typography(i()).action,"typeset_equation")
 def test_semantics(self):self.assertTrue(equation_typography(i()).style["math_semantics_preserved"])
 def test_align(self):self.assertEqual(equation_typography(i(),align="left").style["align"],"left")
 def test_role(self):
  with self.assertRaises(TextVisualValidationError):equation_typography(TextIntent("x","abc","title",("e",),("r",)))
 def test_scale(self):
  with self.assertRaises(TextVisualValidationError):equation_typography(i(),font_scale=3)
 def test_lines(self):
  with self.assertRaises(TextVisualValidationError):equation_typography(i(),max_lines=0)
 def test_display_inline_conflict(self):
  with self.assertRaises(TextVisualValidationError):equation_typography(i("$$x+y$$"),display_mode=False)
 def test_overflow_warning(self):self.assertTrue(equation_typography(i("x"*130),max_lines=1).warnings)
 def test_not_accepted(self):self.assertFalse(equation_typography(i()).accepted)
