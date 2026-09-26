import unittest,ast,pathlib
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.compiler_engine.pipeline import compile_game
class ArchitectureTests(unittest.TestCase):
 def test_bundle_has_15_artifacts(self):self.assertEqual(len(compile_game(compiler_context()).artifacts),15)
 def test_paths_unique(self):
  b=compile_game(compiler_context());self.assertEqual(len({a.path for a in b.artifacts}),len(b.artifacts))
 def test_no_eval_exec_compile_import_dynamic_calls(self):
  root=pathlib.Path(__file__).resolve().parents[2]/'bie/game_engine/compiler_engine';bad=[]
  for p in root.glob('*.py'):
   tree=ast.parse(p.read_text())
   for n in ast.walk(tree):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'eval','exec','compile','__import__'}:bad.append((p.name,n.func.id,n.lineno))
  self.assertEqual(bad,[])
 def test_bundle_is_deterministic(self):self.assertEqual(compile_game(compiler_context()),compile_game(compiler_context()))
 def test_no_remote_network_or_inline_script(self):
  b=compile_game(compiler_context());text='\n'.join(a.content for a in b.artifacts);self.assertNotIn('http://',text);self.assertNotIn('https://',text);self.assertNotIn('eval(',text)
 def test_receipt_binds_all_artifacts(self):
  b=compile_game(compiler_context());self.assertEqual(set(b.receipt.artifact_hashes),{(a.path,a.sha256) for a in b.artifacts})
