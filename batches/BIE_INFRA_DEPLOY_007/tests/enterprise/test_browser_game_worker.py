
import unittest
from enterprise.browser_game_worker import *
class T(unittest.TestCase):
 def m(self):return {"tools":["node","chromium","playwright"],"network_default":"deny","sandbox":True}
 def test_ok(self):self.assertTrue(validate_manifest(self.m()))
 def test_tool(self):
  x=self.m();x["tools"]=[]
  with self.assertRaises(BrowserWorkerError):validate_manifest(x)
 def test_network(self):
  x=self.m();x["network_default"]="allow"
  with self.assertRaises(BrowserWorkerError):validate_manifest(x)
 def test_sandbox(self):
  x=self.m();x["sandbox"]=False
  with self.assertRaises(BrowserWorkerError):validate_manifest(x)
if __name__=="__main__":unittest.main()
