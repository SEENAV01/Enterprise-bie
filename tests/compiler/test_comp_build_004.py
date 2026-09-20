import unittest,tempfile
from pathlib import Path
from bie.compiler.generated_lint import *
class T(unittest.TestCase):
 def scan(self,text):
  with tempfile.TemporaryDirectory() as td:
   Path(td,"a.tsx").write_text(text);return lint_generated_sources(td)
 def test_clean(self):self.assertTrue(self.scan("export const x=1;\n").passed)
 def test_eval(self):self.assertFalse(self.scan("eval('x');\n").passed)
 def test_animation(self):self.assertFalse(self.scan("const s={animation: 'x'};\n").passed)
 def test_warning(self):self.assertEqual(self.scan("console.log('x');\n").warning_count,1)
 def test_counts(self):self.assertEqual((self.scan("eval('x');\nconsole.log('x');\n").error_count,self.scan("eval('x');\nconsole.log('x');\n").warning_count),(1,1))
 def test_not_accepted(self):self.assertFalse(self.scan("export const x=1;\n").accepted)
