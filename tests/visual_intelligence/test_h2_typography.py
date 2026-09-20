import unittest
from bie.visual_intelligence.typography_metrics import *
class T(unittest.TestCase):
 def test_ascii(self):self.assertFalse(measure(TypographyRequest("hello world",20,300,100)).overflow)
 def test_wrap(self):self.assertGreater(len(measure(TypographyRequest("one two three four five",20,80,200)).lines),1)
 def test_overflow(self):self.assertTrue(measure(TypographyRequest("x "*50,30,100,30)).overflow)
 def test_fit_shrink(self):self.assertEqual(fit(TypographyRequest("hello world",30,120,80),12)[0],"FIT")
 def test_hindi(self):self.assertGreater(measure_raw("नमस्ते",20),0)
 def test_cjk(self):self.assertGreaterEqual(measure_raw("中文",20),40)
 def test_equation(self):self.assertGreater(measure_raw("x+y=2",20,"equation"),0)
 def test_bad(self):
  with self.assertRaises(TypographyError):measure(TypographyRequest("",20,100,100))
