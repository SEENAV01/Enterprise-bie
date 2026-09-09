
import unittest
from types import SimpleNamespace
from bie.model_gateway.local_model_adapter import *
class R:
 def generate(self,*a):return {"content":"local"}
class T(unittest.TestCase):
 def q(self):return SimpleNamespace(messages=("x",),response_schema=None)
 def test_provider(self):self.assertEqual(LocalModelAdapter(R(),"m").invoke(self.q())["provider"],"local")
 def test_content(self):self.assertEqual(LocalModelAdapter(R(),"m").invoke(self.q())["content"],"local")
 def test_finish(self):self.assertEqual(LocalModelAdapter(R(),"m").invoke(self.q())["finish_reason"],"stop")
 def test_empty(self):
  with self.assertRaises(LocalAdapterError):LocalModelAdapter(R(),"m").invoke(SimpleNamespace(messages=(),response_schema=None))
if __name__=="__main__":unittest.main()
