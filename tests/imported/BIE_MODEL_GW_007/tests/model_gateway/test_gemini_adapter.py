
import unittest
from types import SimpleNamespace
from model_gateway.gemini_adapter import *
class C:
 def generate(self,**k):return {"content":"ok"}
class T(unittest.TestCase):
 def r(self):return SimpleNamespace(messages=("x",),response_schema=None)
 def test_provider(self):self.assertEqual(GeminiAdapter(C(),"g").invoke(self.r())["provider"],"google")
 def test_content(self):self.assertEqual(GeminiAdapter(C(),"g").invoke(self.r())["content"],"ok")
 def test_finish(self):self.assertEqual(GeminiAdapter(C(),"g").invoke(self.r())["finish_reason"],"unknown")
 def test_empty(self):
  with self.assertRaises(AdapterError):GeminiAdapter(C(),"g").invoke(SimpleNamespace(messages=(),response_schema=None))
if __name__=="__main__":unittest.main()
