import unittest,tempfile
from pathlib import Path
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.build_runtime_engine.pipeline import build_runtime_package
class Pipeline(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.td=tempfile.TemporaryDirectory();ctx,assets=build_inputs();cls.r=build_runtime_package(ctx,assets,Path(cls.td.name))
 @classmethod
 def tearDownClass(cls):cls.td.cleanup()
 def test_all_five_receipts(self):self.assertEqual(len(self.r.receipts),5)
 def test_receipt_ids_unique(self):self.assertEqual(len({x.receipt_id for x in self.r.receipts}),5)
 def test_all_receipts_deterministic(self):self.assertTrue(all(x.deterministic for x in self.r.receipts))
 def test_browser_and_replay_green(self):self.assertTrue(self.r.browser.studio_grade);self.assertTrue(self.r.replay.success)
 def test_both_exception_origins(self):self.assertEqual({x.origin for x in self.r.exceptions},{'node','browser'})
 def test_no_product_acceptance(self):self.assertFalse(self.r.product_accepted);self.assertTrue(all(x.product_accepted is False for x in self.r.receipts))
