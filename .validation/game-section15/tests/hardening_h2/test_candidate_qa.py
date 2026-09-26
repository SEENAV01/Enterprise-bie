import unittest,ast
from dataclasses import replace
from pathlib import Path
from bie.game_engine.errors import GameContractError
from bie.game_engine.qa_engine.pipeline import run_game_qa
from bie.game_engine.qa_engine.contracts import GateStatus
from tests.hardening_h2.support import *
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.c=candidate();cls.r=run_game_qa(cls.c)
 def test_all_ten_candidate_gates_pass(self):self.assertTrue(self.r.all_passed);self.assertEqual(len(self.r.results),10)
 def test_pipeline_deterministic(self):self.assertEqual(self.r,run_game_qa(self.c))
 def test_report_bound_to_candidate(self):self.assertTrue(self.r.report_fingerprint.startswith('sha256:'));self.assertFalse(self.r.product_accepted)
 def test_candidate_compile_binding_tamper_rejected(self):
  bad=replace(self.c,document=replace(self.c.document,document_id='game-doc:tampered'))
  with self.assertRaises(GameContractError):bad.validate()
 def test_candidate_runtime_binding_tamper_rejected(self):
  bad_manifest=replace(self.c.runtime_result.manifest,compiler_bundle_fingerprint='sha256:'+'0'*64);bad=replace(self.c,runtime_result=replace(self.c.runtime_result,manifest=bad_manifest))
  with self.assertRaises(GameContractError):bad.validate()
 def test_candidate_objective_binding_tamper_rejected(self):
  bad=replace(self.c,plans=())
  with self.assertRaises(GameContractError):bad.validate()
 def test_benchmark_supplied_not_constructed(self):self.assertEqual(len(self.c.benchmark_records),8);self.assertIs(self.r.results[8].status,GateStatus.PASS)
 def test_pipeline_source_has_no_fixture_imports(self):
  p=Path(__file__).resolve().parents[2]/'bie/game_engine/qa_engine/pipeline.py';tree=ast.parse(p.read_text());mods=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.ImportFrom):mods.append(n.module or '')
  self.assertFalse(any('fixtures' in x for x in mods))
 def test_qa009_source_has_no_strategy_fixture_import(self):
  p=Path(__file__).resolve().parents[2]/'bie/game_engine/qa_engine/qa_009.py';self.assertNotIn('fixtures',p.read_text())
 def test_candidate_fingerprint_changes_with_benchmark(self):
  b=list(self.c.benchmark_records);b[0]=replace(b[0],domain='physics2');bad=replace(self.c,benchmark_records=tuple(b));self.assertNotEqual(self.c.fingerprint(),bad.fingerprint())
 def test_source_root_required(self):
  bad=replace(self.c,source_root=Path('/definitely/missing'))
  with self.assertRaises(GameContractError):bad.validate()
 def test_no_product_acceptance(self):self.assertFalse(self.c.product_accepted);self.assertTrue(all(not x.product_accepted for x in self.r.results))
