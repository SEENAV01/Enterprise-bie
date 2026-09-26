import unittest,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class ArchitectureTests(unittest.TestCase):
 def test_no_dynamic_execution(self):
  bad=[]
  for p in (ROOT/'bie/game_engine/operations_engine').glob('*.py'):
   t=ast.parse(p.read_text())
   for n in ast.walk(t):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'eval','exec','compile','__import__'}:bad.append((p.name,n.func.id))
  self.assertEqual(bad,[])
 def test_runtime_controller_has_sink_boundary(self):
  s=(ROOT/'bie/game_engine/compiler_engine/runtime_controller.py').read_text();self.assertIn('__BIE_GAME_TELEMETRY_SINK__',s);self.assertIn('__BIE_GAME_TELEMETRY_CONFIG__',s)
 def test_telemetry_program_consent_local_only(self):
  from bie.game_engine.compiler_engine.fixtures import compiler_context
  from bie.game_engine.compiler_engine.telemetry_compiler import compile_telemetry
  s=compile_telemetry(compiler_context()).content;self.assertIn('consent_required',s);self.assertIn('local_sink_only',s);self.assertIn('sequence_ids_required',s)
