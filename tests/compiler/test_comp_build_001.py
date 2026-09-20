import unittest,tempfile,json
from pathlib import Path
from bie.compiler.npm_workspace_generation import *
class T(unittest.TestCase):
 def test_generate(self):
  with tempfile.TemporaryDirectory() as td:self.assertTrue(generate_npm_workspace(root=td,package_name="bie-video",files=[("src/a.ts","export const x=1;\n")]).passed)
 def test_private(self):
  with tempfile.TemporaryDirectory() as td:
   generate_npm_workspace(root=td,package_name="bie-video",files=[]);self.assertTrue(json.loads((Path(td)/"package.json").read_text())["private"])
 def test_escape(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(BuildError):generate_npm_workspace(root=td,package_name="bie-video",files=[("../x","x")])
 def test_duplicate(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(BuildError):generate_npm_workspace(root=td,package_name="bie-video",files=[("x","1"),("x","2")])
 def test_bad_name(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(BuildError):generate_npm_workspace(root=td,package_name="BAD NAME",files=[])
 def test_not_accepted(self):
  with tempfile.TemporaryDirectory() as td:self.assertFalse(generate_npm_workspace(root=td,package_name="bie-video",files=[]).accepted)
