import unittest
from bie.pedagogy.bridge_exit_check import check_bridge_exit
class T(unittest.TestCase):
 def test_attempt_gate(self): self.assertFalse(check_bridge_exit({'a':.8},{'a':.9},{'a':2},{'a':1}).passed)
 def test_pass(self): self.assertTrue(check_bridge_exit({'a':.8},{'a':.9},achieved_attempts={'a':1}).passed)
