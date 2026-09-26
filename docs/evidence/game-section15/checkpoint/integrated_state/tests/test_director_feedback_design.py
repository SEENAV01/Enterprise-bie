import unittest
from dataclasses import replace
from bie.game_engine.director_engine.feedback_design import design_feedback
from tests.director_test_support import ctx
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_valid(self):
  out=design_feedback(ctx());self.assertIsNotNone(out)
 def test_deterministic(self):self.assertEqual(design_feedback(ctx()),design_feedback(ctx()))
 def test_missing_selected_strategy_or_provenance_fails(self):
  c=ctx();bad=replace(c,provenance=replace(c.provenance,refs=()))
  with self.assertRaises(GameContractError):design_feedback(bad)
 def test_product_acceptance_not_present_as_true(self):self.assertNotIn('product_accepted=True',repr(design_feedback(ctx())))

 def test_never_reveals_answer_before_attempt(self):self.assertTrue(all(x.answer_reveal_before_attempt is False for x in design_feedback(ctx())))

if __name__=='__main__':unittest.main()
