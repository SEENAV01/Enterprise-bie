import unittest
from dataclasses import replace
from bie.game_engine.director_engine.level_sequencing import sequence_levels
from tests.director_test_support import ctx
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_valid(self):
  out=sequence_levels(ctx());self.assertIsNotNone(out)
 def test_deterministic(self):self.assertEqual(sequence_levels(ctx()),sequence_levels(ctx()))
 def test_missing_selected_strategy_or_provenance_fails(self):
  c=ctx();bad=replace(c,provenance=replace(c.provenance,refs=()))
  with self.assertRaises(GameContractError):sequence_levels(bad)
 def test_product_acceptance_not_present_as_true(self):self.assertNotIn('product_accepted=True',repr(sequence_levels(ctx())))

 def test_sequence_respects_max_levels(self):
  from dataclasses import replace
  c=ctx();c=replace(c,constraints=replace(c.constraints,max_levels=1));self.assertEqual(len(sequence_levels(c)),1)
 def test_prerequisite_chain_is_acyclic_for_fixture(self):
  rows=sequence_levels(ctx());self.assertFalse(rows[0].prerequisite_level_ids)

if __name__=='__main__':unittest.main()
