
import unittest
from types import SimpleNamespace
from model_gateway.claude_adapter import *
class C:
 def messages_create(self,**k):return {"content":"ok"}
class T(unittest.TestCase):
 def r(self):return SimpleNamespace(messages=("x",),response_schema=None)
 def test_provider(self):self.assertEqual(ClaudeAdapter(C(),"c").invoke(self.r())["provider"],"anthropic")
 def test_model(self):self.assertEqual(ClaudeAdapter(C(),"c").invoke(self.r())["model"],"c")
 def test_content(self):self.assertEqual(ClaudeAdapter(C(),"c").invoke(self.r())["content"],"ok")
 def test_empty(self):
  with self.assertRaises(AdapterError):ClaudeAdapter(C(),"c").invoke(SimpleNamespace(messages=(),response_schema=None))
if __name__=="__main__":unittest.main()
