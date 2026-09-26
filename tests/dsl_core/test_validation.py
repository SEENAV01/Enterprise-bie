import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.fixtures import sample_document
from bie.game_engine.validation import validate_game_document
class T(unittest.TestCase):
 def test_validate(self):
  out,r=validate_game_document(sample_document());self.assertTrue(out['wire_roundtrip']);self.assertTrue(out['studio_grade_intent']);self.assertFalse(out['product_accepted']);self.assertFalse(r.product_accepted)
 def test_wrong_type(self):
  with self.assertRaises(GameContractError):validate_game_document({})
 def test_stable(self):
  self.assertEqual(validate_game_document(sample_document())[0],validate_game_document(sample_document())[0])
