import unittest,tempfile,json,shutil
from pathlib import Path
from bie.compiler.dependency_lock import *
class T(unittest.TestCase):
 def ws(self,td):
  p=Path(td);(p/"package.json").write_text(json.dumps({"name":"x","version":"0.0.0","private":True,"dependencies":{},"devDependencies":{}}));return p
 def test_actual_lock(self):
  if shutil.which("npm") is None:self.skipTest("npm unavailable")
  with tempfile.TemporaryDirectory() as td:self.assertTrue(create_dependency_lock(self.ws(td)).passed)
 def test_validate(self):
  with tempfile.TemporaryDirectory() as td:
   p=self.ws(td);(p/"package-lock.json").write_text(json.dumps({"name":"x","version":"0.0.0","lockfileVersion":3,"packages":{"":{"dependencies":{},"devDependencies":{}}}}));self.assertTrue(validate_package_lock(p/"package-lock.json",p/"package.json").passed)
 def test_name_mismatch(self):
  with tempfile.TemporaryDirectory() as td:
   p=self.ws(td);(p/"package-lock.json").write_text(json.dumps({"name":"y","lockfileVersion":3,"packages":{"":{}}}))
   with self.assertRaises(BuildError):validate_package_lock(p/"package-lock.json",p/"package.json")
 def test_version(self):
  with tempfile.TemporaryDirectory() as td:
   p=self.ws(td);(p/"package-lock.json").write_text(json.dumps({"name":"x","lockfileVersion":1,"packages":{"":{}}}))
   with self.assertRaises(BuildError):validate_package_lock(p/"package-lock.json",p/"package.json")
 def test_not_accepted(self):
  with tempfile.TemporaryDirectory() as td:
   p=self.ws(td);(p/"package-lock.json").write_text(json.dumps({"name":"x","lockfileVersion":3,"packages":{"":{"dependencies":{},"devDependencies":{}}}}));self.assertFalse(validate_package_lock(p/"package-lock.json",p/"package.json").accepted)
