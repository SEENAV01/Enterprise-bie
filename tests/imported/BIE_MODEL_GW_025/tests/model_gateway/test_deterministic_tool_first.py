
import unittest
from model_gateway.deterministic_tool_first import *
class T(unittest.TestCase):
 def test_math(self):self.assertEqual(route("arithmetic",True),"TOOL")
 def test_hash(self):self.assertEqual(route("hashing",True),"TOOL")
 def test_missing_tool(self):self.assertEqual(route("arithmetic",False),"MODEL")
 def test_reason(self):self.assertEqual(route("pedagogical_reasoning",True),"MODEL")
 def test_empty(self):
  with self.assertRaises(ToolFirstError):route("",True)
if __name__=="__main__":unittest.main()
