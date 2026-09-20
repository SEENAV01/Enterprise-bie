import unittest
from bie.animation_intelligence.attention_contracts import *
from bie.animation_intelligence.attention_model import *
def t(i,imp,m=.0,v=.0,active=True):return AttentionTarget(i,"diagram",imp,("e",),("r",),m,v,active)
class T(unittest.TestCase):
 def test_primary(self):self.assertEqual(build_attention_model([t("a",.9),t("b",.5)]).primary_target,"a")
 def test_secondary(self):self.assertEqual(build_attention_model([t("a",.9),t("b",.7)]).secondary_targets,("b",))
 def test_motion_penalty(self):self.assertEqual(build_attention_model([t("a",.4,m=.95),t("b",.6)]).primary_target,"b")
 def test_inactive(self):self.assertEqual(build_attention_model([t("a",.9,active=False),t("b",.5)]).primary_target,"b")
 def test_none_active(self):self.assertEqual(build_attention_model([t("a",.9,active=False)]).status,"UNSUPPORTED")
 def test_duplicate(self):
  with self.assertRaises(AttentionError):build_attention_model([t("a",.9),t("a",.5)])
 def test_deterministic(self):self.assertEqual(build_attention_model([t("a",.9)]).fingerprint,build_attention_model([t("a",.9)]).fingerprint)
 def test_not_accepted(self):self.assertFalse(build_attention_model([t("a",.9)]).accepted)
