import unittest,json
from bie.compiler.react_project_emitter import *
class T(unittest.TestCase):
 def emit(self):return emit_react_project(project_name="bie-video",remotion_version="4.0.0",react_version="19.0.0",typescript_version="5.9.0")
 def test_files(self):self.assertEqual([f.path for f in self.emit()],["package.json","remotion.config.ts","src/index.ts","tsconfig.json"])
 def test_package(self):
  p=json.loads(next(f.content for f in self.emit() if f.path=="package.json"));self.assertEqual(p["dependencies"]["remotion"],"4.0.0");self.assertTrue(p["private"])
 def test_studio_no_open(self):self.assertIn("studio --no-open",next(f.content for f in self.emit() if f.path=="package.json"))
 def test_strict_ts(self):self.assertTrue(json.loads(next(f.content for f in self.emit() if f.path=="tsconfig.json"))["compilerOptions"]["strict"])
 def test_conflict(self):
  with self.assertRaises(ReactEmitterError):emit_react_project(project_name="x",remotion_version="4",react_version="19",typescript_version="5",extra_dependencies={"react":"20"})
 def test_hashes(self):self.assertTrue(all(len(f.sha256)==64 for f in self.emit()))
