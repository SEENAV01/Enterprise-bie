import unittest,ast
from pathlib import Path
from tests.hardening_h4.support import context
ROOT=Path(__file__).resolve().parents[2]
class ArchitectureTests(unittest.TestCase):
 def test_no_dynamic_eval(self):
  bad=[]
  for p in (ROOT/'bie/game_engine/runtime_quality_engine').glob('*.py'):
   tree=ast.parse(p.read_text())
   for n in ast.walk(tree):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'eval','exec','compile','__import__'}:bad.append((p.name,n.func.id))
  self.assertEqual(bad,[])
 def test_profile_is_optional_for_legacy(self):
  from tests.hardening_h2.support import compiler_context
  self.assertIsNone(compiler_context().experience_profile)
 def test_h4_context_profile_bound(self):self.assertIsNotNone(context().experience_profile)
