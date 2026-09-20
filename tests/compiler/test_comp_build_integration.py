import unittest,tempfile,json,shutil
from pathlib import Path
from bie.compiler.npm_workspace_generation import generate_npm_workspace
from bie.compiler.dependency_lock import create_dependency_lock
from bie.compiler.typescript_compile import compile_typescript
from bie.compiler.generated_lint import lint_generated_sources
from bie.compiler.generated_static_analysis import analyze_generated_sources
from bie.compiler.remotion_composition_discovery import discover_compositions_static
class T(unittest.TestCase):
 def test_real_local_build_fixture(self):
  if shutil.which("npm") is None or shutil.which("tsc") is None:self.skipTest("npm/tsc unavailable")
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   generate_npm_workspace(root=root,package_name="bie-build-fixture",files=[("src/a.ts","export const x:number=1;\n"),("src/Composition.tsx",'<Composition id={"Lesson"} component={Scene} width={1920} height={1080} fps={30} durationInFrames={300} />;\n'),("tsconfig.json",json.dumps({"compilerOptions":{"strict":True,"target":"ES2020","module":"ESNext","noEmit":True,"jsx":"preserve"},"include":["src/a.ts"]}))])
   self.assertTrue(create_dependency_lock(root).passed)
   self.assertTrue(compile_typescript(root).passed)
   self.assertTrue(lint_generated_sources(root/"src").passed)
   self.assertTrue(analyze_generated_sources(root/"src").passed)
   d=discover_compositions_static((root/"src/Composition.tsx").read_text());self.assertTrue(d.passed);self.assertEqual(d.compositions[0].composition_id,"Lesson")
 def test_no_render_claim(self):
  self.assertFalse(discover_compositions_static('<Composition id={"A"} component={S} width={1} height={1} fps={1} durationInFrames={1} />').accepted)
