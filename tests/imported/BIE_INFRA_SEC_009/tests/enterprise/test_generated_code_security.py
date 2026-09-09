
import unittest
from bie.infrastructure.generated_code_security import *
class T(unittest.TestCase):
 def test_safe(self):self.assertTrue(assert_safe("const x = 1;"))
 def test_eval(self):
  with self.assertRaises(GeneratedCodeSecurityError):assert_safe("eval(x)")
 def test_child(self):self.assertFalse(scan("require('child_process')")["passed"])
 def test_env(self):self.assertFalse(scan("process.env.KEY")["passed"])
 def test_write(self):self.assertFalse(scan("fs.writeFile(x)")["passed"])
if __name__=="__main__":unittest.main()
