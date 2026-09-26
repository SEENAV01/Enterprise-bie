import unittest
from bie.game_engine.director_engine.pipeline import run_director_pipeline
from tests.director_test_support import ctx
class Tests(unittest.TestCase):
 def test_pipeline(self):
  x=run_director_pipeline(ctx());self.assertFalse(x['product_accepted']);self.assertEqual(x['plan_fingerprint'],x['plan'].plan_fingerprint)
 def test_pipeline_deterministic(self):self.assertEqual(run_director_pipeline(ctx())['deterministic_receipt'],run_director_pipeline(ctx())['deterministic_receipt'])
