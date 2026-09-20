import unittest,tempfile
from pathlib import Path
from bie.compiler.generated_static_analysis import *
class T(unittest.TestCase):
 def scan(self,text):
  with tempfile.TemporaryDirectory() as td:
   Path(td,"a.tsx").write_text(text);return analyze_generated_sources(td)
 def test_clean(self):self.assertTrue(self.scan('import React from "react";\n').passed)
 def test_child(self):self.assertFalse(self.scan('import x from "child_process";\n').passed)
 def test_fs(self):self.assertFalse(self.scan('import fs from "fs";\n').passed)
 def test_remote(self):self.assertFalse(self.scan('staticFile("https://x");\n').passed)
 def test_review(self):self.assertEqual(self.scan("const x=process.env.KEY;\n").findings[0].severity,"REVIEW")
 def test_not_accepted(self):self.assertFalse(self.scan("export const x=1;\n").accepted)
