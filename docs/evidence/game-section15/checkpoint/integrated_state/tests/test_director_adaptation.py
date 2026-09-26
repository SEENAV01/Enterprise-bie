import unittest
from dataclasses import replace
from bie.game_engine.director_engine.adaptation import design_adaptation
from tests.director_test_support import ctx
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_valid(self):
  out=design_adaptation(ctx());self.assertIsNotNone(out)
 def test_deterministic(self):self.assertEqual(design_adaptation(ctx()),design_adaptation(ctx()))
 def test_missing_selected_strategy_or_provenance_fails(self):
  c=ctx();bad=replace(c,provenance=replace(c.provenance,refs=()))
  with self.assertRaises(GameContractError):design_adaptation(bad)
 def test_product_acceptance_not_present_as_true(self):self.assertNotIn('product_accepted=True',repr(design_adaptation(ctx())))

 def test_priority_is_deterministic_and_explainable(self):
  rows=design_adaptation(ctx());self.assertEqual([x.priority for x in rows],sorted(x.priority for x in rows));self.assertTrue(all(x.rationale for x in rows))

if __name__=='__main__':unittest.main()
