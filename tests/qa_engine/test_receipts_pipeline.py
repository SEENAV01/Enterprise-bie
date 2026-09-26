import unittest
from pathlib import Path
from dataclasses import replace
from bie.game_engine.qa_engine.pipeline import run_game_qa
from bie.game_engine.qa_engine.receipts import make_receipt
from bie.game_engine.qa_engine.contracts import GateStatus
from tests.qa_engine.support import ROOT
from tests.hardening_h2.support import candidate
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.c=candidate();cls.r=run_game_qa(cls.c)
 def test_pipeline_all_passed(self):self.assertTrue(self.r.all_passed)
 def test_exact_ten_results(self):self.assertEqual(len(self.r.results),10)
 def test_ids_complete(self):self.assertEqual([x.task_id for x in self.r.results],[f'BIE-GAME-QA-{i:03d}' for i in range(1,11)])
 def test_deterministic_pipeline(self):self.assertEqual(self.r,run_game_qa(self.c))
 def test_receipt_deterministic(self):
  a=make_receipt(self.r.results[0],'impl');b=make_receipt(self.r.results[0],'impl');self.assertEqual(a,b)
 def test_no_product_acceptance(self):self.assertFalse(self.r.product_accepted);self.assertTrue(all(not x.product_accepted for x in self.r.results))
 def test_report_fingerprint(self):self.assertTrue(self.r.report_fingerprint.startswith('sha256:'))
