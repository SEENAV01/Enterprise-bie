import unittest
from bie.visual_intelligence.access_contracts import *
from bie.visual_intelligence.contrast import *
def i():return VisualAccessIntent("i","body",("e",),("r",))
class T(unittest.TestCase):
 def test_black_white(self): self.assertAlmostEqual(contrast_ratio("#000000","#FFFFFF"),21.0,places=3)
 def test_pass(self): self.assertEqual(evaluate_contrast(i(),foreground="#000000",background="#FFFFFF").action,"contrast_pass")
 def test_fail(self): self.assertEqual(evaluate_contrast(i(),foreground="#777777",background="#888888").action,"contrast_revise")
 def test_large_threshold(self): self.assertEqual(evaluate_contrast(i(),foreground="#767676",background="#FFFFFF",large_text=True).payload["threshold"],3.0)
 def test_enhanced(self): self.assertEqual(evaluate_contrast(i(),foreground="#000000",background="#FFFFFF",enhanced=True).payload["threshold"],7.0)
 def test_bad_hex(self):
  with self.assertRaises(ContrastError): contrast_ratio("red","#ffffff")
 def test_warning(self): self.assertTrue(evaluate_contrast(i(),foreground="#777777",background="#888888").warnings)
 def test_not_accepted(self): self.assertFalse(evaluate_contrast(i(),foreground="#000000",background="#FFFFFF").accepted)
 def test_deterministic(self):
  a=evaluate_contrast(i(),foreground="#000000",background="#FFFFFF"); b=evaluate_contrast(i(),foreground="#000000",background="#FFFFFF"); self.assertEqual(a.fingerprint,b.fingerprint)
