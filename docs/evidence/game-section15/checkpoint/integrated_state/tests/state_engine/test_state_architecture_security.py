import unittest,ast
from pathlib import Path

class StateArchitectureSecurityTests(unittest.TestCase):
 def test_no_eval_exec_compile_import_calls(self):
  root=Path(__file__).resolve().parents[2]/'bie/game_engine/state_engine';bad=[]
  for p in root.glob('*.py'):
   tree=ast.parse(p.read_text())
   for n in ast.walk(tree):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'eval','exec','compile','__import__'}:bad.append((p.name,n.func.id))
  self.assertEqual(bad,[])
 def test_task_modules_exist(self):
  root=Path(__file__).resolve().parents[2]/'bie/game_engine/state_engine'
  for name in ('state_variables.py','manipulables.py','rules.py','effects.py','challenge_state.py','conditions.py','reachability.py'):self.assertTrue((root/name).is_file())
 def test_cross_cutting_modules_exist(self):
  root=Path(__file__).resolve().parents[2]/'bie/game_engine/state_engine'
  for name in ('snapshots.py','expression_runtime.py','transition_engine.py','receipts.py','replay.py','invariants.py'):self.assertTrue((root/name).is_file())
