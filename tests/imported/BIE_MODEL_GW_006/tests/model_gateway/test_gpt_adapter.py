
import unittest
from types import SimpleNamespace
from bie.model_gateway.gpt_adapter import *
class C:
 def responses_create(self,**k):return {"content":"ok","usage":{"in":1},"finish_reason":"stop"}
class T(unittest.TestCase):
 def req(self):return SimpleNamespace(messages=("x",),response_schema=None)
 def test_provider(self):self.assertEqual(GPTAdapter(C(),"g").invoke(self.req())["provider"],"openai")
 def test_model(self):self.assertEqual(GPTAdapter(C(),"g").invoke(self.req())["model"],"g")
 def test_content(self):self.assertEqual(GPTAdapter(C(),"g").invoke(self.req())["content"],"ok")
 def test_empty(self):
  with self.assertRaises(AdapterError):GPTAdapter(C(),"g").invoke(SimpleNamespace(messages=(),response_schema=None))
if __name__=="__main__":unittest.main()
