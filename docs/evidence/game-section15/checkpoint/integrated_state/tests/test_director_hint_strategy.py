import unittest
from dataclasses import replace
from bie.game_engine.director_engine.hint_strategy import design_hints
from tests.director_test_support import ctx
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_valid(self):
  out=design_hints(ctx());self.assertIsNotNone(out)
 def test_deterministic(self):self.assertEqual(design_hints(ctx()),design_hints(ctx()))
 def test_missing_selected_strategy_or_provenance_fails(self):
  c=ctx();bad=replace(c,provenance=replace(c.provenance,refs=()))
  with self.assertRaises(GameContractError):design_hints(bad)
 def test_product_acceptance_not_present_as_true(self):self.assertNotIn('product_accepted=True',repr(design_hints(ctx())))

 def test_progressive_reveal_stays_below_answer(self):
  rows=design_hints(ctx());self.assertTrue(all(x.reveal_fraction<1 for x in rows));self.assertEqual([x.level for x in rows],[1,2,3,4])

if __name__=='__main__':unittest.main()
