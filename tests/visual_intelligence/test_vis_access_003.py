import unittest
from bie.visual_intelligence.access_contracts import *
from bie.visual_intelligence.color_independent_encoding import *
def i():return VisualAccessIntent("i","chart",("e",),("r",))
class T(unittest.TestCase):
 def test_pass(self):
  d=evaluate_color_independent_encoding(i(),categories=["A","B"],color_map={"A":"red","B":"blue"},
    secondary_encodings={"A":["shape"],"B":["label"]}); self.assertTrue(d.payload["passes"])
 def test_fail(self):
  d=evaluate_color_independent_encoding(i(),categories=["A"],color_map={"A":"red"},secondary_encodings={"A":[]}); self.assertEqual(d.action,"add_noncolor_encoding")
 def test_missing(self):
  self.assertEqual(evaluate_color_independent_encoding(i(),categories=["A"],color_map={"A":"red"},secondary_encodings={"A":[]}).payload["missing_secondary"],["A"])
 def test_bad_cover(self):
  with self.assertRaises(EncodingError): evaluate_color_independent_encoding(i(),categories=["A"],color_map={},secondary_encodings={"A":["shape"]})
 def test_bad_encoding(self):
  with self.assertRaises(EncodingError): evaluate_color_independent_encoding(i(),categories=["A"],color_map={"A":"red"},secondary_encodings={"A":["blink"]})
 def test_duplicate_cat(self):
  with self.assertRaises(EncodingError): evaluate_color_independent_encoding(i(),categories=["A","A"],color_map={"A":"red"},secondary_encodings={"A":["shape"]})
 def test_warning(self): self.assertTrue(evaluate_color_independent_encoding(i(),categories=["A"],color_map={"A":"red"},secondary_encodings={"A":[]}).warnings)
 def test_review(self): self.assertTrue(evaluate_color_independent_encoding(i(),categories=["A"],color_map={"A":"red"},secondary_encodings={"A":["shape"]}).review_required)
