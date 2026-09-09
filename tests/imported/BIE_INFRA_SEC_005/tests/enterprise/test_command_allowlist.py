
import unittest
from bie.infrastructure.command_allowlist import *
class T(unittest.TestCase):
 def setUp(self):self.p=CommandPolicy({"node","npm"})
 def test_ok(self):self.assertEqual(self.p.validate(["node","x.js"])[0],"node")
 def test_string(self):
  with self.assertRaises(CommandSecurityError):self.p.validate("node x.js")
 def test_denied(self):
  with self.assertRaises(CommandSecurityError):self.p.validate(["bash","x"])
 def test_meta(self):
  with self.assertRaises(CommandSecurityError):self.p.validate(["node","x;rm"])
 def test_empty(self):
  with self.assertRaises(CommandSecurityError):self.p.validate([])
if __name__=="__main__":unittest.main()
