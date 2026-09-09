
import unittest
from model_gateway.tool_call_contract import *
class T(unittest.TestCase):
 def c(self):return ToolCall("search",{},"1")
 def test_ok(self):self.assertTrue(validate_call(self.c(),{"search"}))
 def test_deny(self):
  with self.assertRaises(ToolCallError):validate_call(self.c(),{"calc"})
 def test_id(self):
  with self.assertRaises(ToolCallError):validate_call(ToolCall("search",{},""),{"search"})
 def test_bind(self):self.assertTrue(bind_result(self.c(),ToolResult("1",True,"x")).ok)
 def test_mismatch(self):
  with self.assertRaises(ToolCallError):bind_result(self.c(),ToolResult("2",True,"x"))
if __name__=="__main__":unittest.main()
