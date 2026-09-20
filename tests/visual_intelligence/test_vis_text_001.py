import unittest
from bie.visual_intelligence.text_contracts import *
from bie.visual_intelligence.on_screen_text_selection import *
def i(text="Hello world",role="title",req=True,maxc=140):return TextIntent("t",text,role,("e",),("r",),req,50,maxc)
class T(unittest.TestCase):
 def test_show(self):self.assertEqual(select_on_screen_text(i()).action,"show_text")
 def test_normalize(self):self.assertEqual(select_on_screen_text(i("a   b")).display_text,"a b")
 def test_condense(self):self.assertEqual(select_on_screen_text(i("x"*30),available_char_budget=10).action,"show_condensed_text")
 def test_required_escalate(self):self.assertEqual(select_on_screen_text(i("x"*30),available_char_budget=10,allow_condense=False).action,"escalate_text_overflow")
 def test_optional_omit(self):self.assertEqual(select_on_screen_text(i("x"*30,req=False),available_char_budget=10,allow_condense=False).action,"omit_optional_text")
 def test_role(self):
  with self.assertRaises(TextVisualValidationError):select_on_screen_text(i(role="magic"))
 def test_budget(self):
  with self.assertRaises(TextVisualValidationError):select_on_screen_text(i(),available_char_budget=0)
 def test_not_accepted(self):self.assertFalse(select_on_screen_text(i()).accepted)
 def test_grounding(self):self.assertEqual(i().evidence_refs,("e",))
