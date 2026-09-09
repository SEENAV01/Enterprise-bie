
import unittest
from bie.infrastructure.execution_sandbox import *
class T(unittest.TestCase):
 def test_valid(self):self.assertEqual(execution_env(SandboxPolicy(10,128,2,False))["network"],False)
 def test_cpu(self):
  with self.assertRaises(SandboxError):validate_policy(SandboxPolicy(0,128,1,False))
 def test_mem(self):
  with self.assertRaises(SandboxError):validate_policy(SandboxPolicy(1,32,1,False))
 def test_proc(self):
  with self.assertRaises(SandboxError):validate_policy(SandboxPolicy(1,64,0,False))
if __name__=="__main__":unittest.main()
