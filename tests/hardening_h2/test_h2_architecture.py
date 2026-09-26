import unittest,ast
from pathlib import Path
from bie.game_engine.handoff_engine.canonical_adapters import CANONICAL_BLOBS
ROOT=Path(__file__).resolve().parents[2]
class Tests(unittest.TestCase):
 def test_three_h2_subsystems_exist(self):
  for p in ('handoff_engine/materializer.py','handoff_engine/canonical_adapters.py','qa_engine/candidate.py'):self.assertTrue((ROOT/'bie/game_engine'/p).exists())
 def test_production_qa_pipeline_not_fixture_bound(self):self.assertNotIn('fixtures', (ROOT/'bie/game_engine/qa_engine/pipeline.py').read_text())
 def test_no_dynamic_eval_in_h2(self):
  hits=[]
  for p in list((ROOT/'bie/game_engine/handoff_engine').glob('*.py'))+[ROOT/'bie/game_engine/qa_engine/candidate.py',ROOT/'bie/game_engine/qa_engine/pipeline.py']:
   tree=ast.parse(p.read_text())
   for n in ast.walk(tree):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'eval','exec','compile','__import__'}:hits.append((p.name,n.func.id))
  self.assertEqual(hits,[])
 def test_canonical_paths_pinned(self):self.assertEqual({p for p,_ in CANONICAL_BLOBS},{'bie/director/game_handoff.py','bie/reasoning/game_decision.py','bie/pedagogy/pedagogy_plan_contract.py'})
 def test_h2_never_claims_product_acceptance(self):
  text='\n'.join(p.read_text() for p in (ROOT/'bie/game_engine/handoff_engine').glob('*.py'))+'\n'+(ROOT/'bie/game_engine/qa_engine/candidate.py').read_text();self.assertNotIn('product_accepted=True',text)
