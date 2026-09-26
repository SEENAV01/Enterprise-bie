import unittest, pathlib, ast
from bie.game_engine.mechanics_engine.contracts import *
from bie.game_engine.mechanics_engine.common import sample_context
from bie.game_engine.mechanics_engine.pipeline import define
from bie.game_engine.mechanics_engine.studio_policy import validate_studio_mechanic
class ArchitectureTests(unittest.TestCase):
 def test_all_17_kinds_have_dispatch(self):
  self.assertEqual(len(MechanicKind),17)
  for k in MechanicKind:self.assertIsNotNone(define(k,sample_context()))
 def test_all_definitions_studio_policy(self):
  for k in MechanicKind:self.assertEqual(validate_studio_mechanic(define(k,sample_context())),define(k,sample_context()))
 def test_dynamic_actions_keyboard_parity(self):
  for k in MechanicKind:
   d=define(k,sample_context())
   for a in d.actions:
    if a.action_kind in {ActionKind.DRAG,ActionKind.DROP,ActionKind.ADJUST,ActionKind.PLACE,ActionKind.ORDER}:self.assertTrue(a.keyboard_equivalent)
 def test_no_dynamic_eval_exec_compile_import(self):
  root=pathlib.Path(__file__).resolve().parents[2]/'bie/game_engine/mechanics_engine';bad=[]
  for p in root.glob('*.py'):
   tree=ast.parse(p.read_text())
   for n in ast.walk(tree):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'eval','exec','compile','__import__'}:bad.append((p.name,n.func.id))
  self.assertEqual(bad,[])
 def test_product_acceptance_false_everywhere(self):
  for k in MechanicKind:self.assertFalse(define(k,sample_context()).product_accepted)
