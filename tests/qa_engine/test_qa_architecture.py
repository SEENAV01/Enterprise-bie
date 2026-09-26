import unittest,ast
from pathlib import Path
from tests.qa_engine.support import ROOT
class Tests(unittest.TestCase):
 def test_ten_capability_modules_exist(self):self.assertEqual(len(list((ROOT/'bie/game_engine/qa_engine').glob('qa_0*.py'))),10)
 def test_no_dynamic_eval_in_qa_engine(self):
  hits=[]
  for p in (ROOT/'bie/game_engine/qa_engine').glob('*.py'):
   tree=ast.parse(p.read_text())
   for n in ast.walk(tree):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'eval','exec','compile','__import__'}:hits.append((p.name,n.func.id))
  self.assertEqual(hits,[])
 def test_pipeline_not_section16_acceptance(self):self.assertNotIn('product_accepted=True',(ROOT/'bie/game_engine/qa_engine/pipeline.py').read_text())
 def test_no_keyword_generator_function(self):
  text='\n'.join(p.read_text().lower() for p in (ROOT/'bie/game_engine/qa_engine').glob('*.py'));self.assertNotIn('def keyword_game_generator',text)
 def test_policy_is_explicit(self):self.assertTrue((ROOT/'bie/game_engine/qa_engine/policy.py').exists())
