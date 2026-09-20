import unittest,tempfile,json,shutil
from pathlib import Path
from bie.compiler.typescript_compile import *
class T(unittest.TestCase):
 def ws(self,td,src):
  p=Path(td);(p/"src").mkdir();(p/"src/a.ts").write_text(src);(p/"tsconfig.json").write_text(json.dumps({"compilerOptions":{"strict":True,"target":"ES2020","module":"ESNext","noEmit":True},"include":["src/**/*.ts"]}));return p
 def test_actual_pass(self):
  if shutil.which("tsc") is None:self.skipTest("tsc unavailable")
  with tempfile.TemporaryDirectory() as td:self.assertTrue(compile_typescript(self.ws(td,"const x:number=1;\n")).passed)
 def test_actual_fail(self):
  if shutil.which("tsc") is None:self.skipTest("tsc unavailable")
  with tempfile.TemporaryDirectory() as td:self.assertFalse(compile_typescript(self.ws(td,'const x:number="bad";\n')).passed)
 def test_parse(self):self.assertEqual(parse_tsc_diagnostics("a.ts(1,1): error TS2322: Bad")[0].code,"TS2322")
 def test_missing(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(BuildError):compile_typescript(td)
 def test_not_accepted(self):
  if shutil.which("tsc") is None:self.skipTest("tsc unavailable")
  with tempfile.TemporaryDirectory() as td:self.assertFalse(compile_typescript(self.ws(td,"const x=1;\n")).accepted)
