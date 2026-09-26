import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.fixtures import sample_document
from bie.game_engine.codec import *
class T(unittest.TestCase):
 def test_roundtrip(self):
  d=sample_document();self.assertEqual(loads(dumps(d)),d)
 def test_deterministic_wire(self):self.assertEqual(dumps(sample_document()),dumps(sample_document()))
 def test_unknown_type(self):
  with self.assertRaises(GameContractError):loads('{"$type":"X"}')
 def test_unknown_enum(self):
  with self.assertRaises(GameContractError):loads('{"$enum":"X","value":"y"}')
 def test_unknown_field(self):
  import json
  raw=encode(sample_document());raw['extra']=1
  with self.assertRaises(GameContractError):decode(raw)
 def test_bad_json(self):
  with self.assertRaises(GameContractError):loads('{')
 def test_expr_roundtrip(self):
  from bie.game_engine.expressions import Compare,CompareOp,Variable,Literal
  e=Compare(CompareOp.EQ,Variable('x'),Literal(2));self.assertEqual(decode(encode(e)),e)
