
import unittest,json
from bie.infrastructure.structured_logs import *
class T(unittest.TestCase):
 def test_make(self): self.assertEqual(make_log("INFO","start","r").level,"INFO")
 def test_bad_level(self):
  with self.assertRaises(LogError): make_log("X","e","r")
 def test_required(self):
  with self.assertRaises(LogError): make_log("INFO","","r")
 def test_secret(self):
  with self.assertRaises(LogError): make_log("INFO","e","r",api_key="x")
 def test_json(self): self.assertEqual(json.loads(encode(make_log("INFO","e","r")))["run_id"],"r")
if __name__=="__main__": unittest.main()
