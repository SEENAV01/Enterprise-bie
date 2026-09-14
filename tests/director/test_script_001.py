import unittest
from bie.director.script_plan import *
class T(unittest.TestCase):
    def test_deterministic(self):
        a=ScriptSegment("a","s","EXPLAIN","x",("e",),("o",)); b=ScriptSegment("b","s","RECAP","y",("e",),("o",))
        self.assertEqual(build_script_plan("l",[b,a],"teacher").fingerprint(),build_script_plan("l",[a,b],"teacher").fingerprint())
