import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.ids import *
from bie.game_engine.canonical import canonical_json,fingerprint
class T(unittest.TestCase):
 def test_id(self):self.assertEqual(require_id('a:b-c_1'),'a:b-c_1')
 def test_bad_ids(self):
  for v in ('',' bad','a b','a'*300):
   with self.assertRaises(GameContractError):require_id(v)
 def test_text(self):self.assertEqual(require_text('purposeful motion'),'purposeful motion')
 def test_bad_text(self):
  with self.assertRaises(GameContractError):require_text('   ')
 def test_semver(self):self.assertEqual(require_semver('2.0.0'),'2.0.0')
 def test_bad_semver(self):
  for v in ('2','02.0.0','2.0','v2.0.0'):
   with self.assertRaises(GameContractError):require_semver(v)
 def test_sha(self):self.assertEqual(require_sha256('a'*64),'a'*64)
 def test_bad_sha(self):
  with self.assertRaises(GameContractError):require_sha256('A'*64)
 def test_canonical_dict_order(self):self.assertEqual(canonical_json({'b':2,'a':1}),canonical_json({'a':1,'b':2}))
 def test_fingerprint_stable(self):self.assertEqual(fingerprint({'a':[1,2]}),fingerprint({'a':[1,2]}))
 def test_nonfinite_rejected(self):
  with self.assertRaises(GameContractError):canonical_json(float('nan'))
