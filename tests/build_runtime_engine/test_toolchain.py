import unittest
from bie.game_engine.build_runtime_engine.toolchain import discover_toolchain
class Toolchain(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.tools,cls.fp=discover_toolchain()
 def test_required_tools(self):self.assertEqual({x.name for x in self.tools},{'python','node','typescript','chromium'})
 def test_all_tool_hashes(self):self.assertTrue(all(len(x.executable_sha256)==64 for x in self.tools))
 def test_toolchain_fingerprint(self):self.assertTrue(self.fp.startswith('sha256:'))
 def test_toolchain_repeatable(self):self.assertEqual(self.fp,discover_toolchain()[1])
