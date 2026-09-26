import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.schema_registry import *
from bie.game_engine.compatibility import *
from bie.game_engine.receipts import *
from bie.game_engine.fixtures import sample_document
class T(unittest.TestCase):
 def test_current(self):self.assertEqual(resolve('2.0.0').status,'current')
 def test_legacy_readonly(self):self.assertEqual(resolve('1.0.0').status,'read_only_legacy')
 def test_unknown(self):
  with self.assertRaises(GameContractError):resolve('9.0.0')
 def test_legacy_inspect(self):
  v={'game_ir_version':'1.0.0','document_id':'d','experiences':[{'levels':[]}],'source_artifact_refs':['s'],'reasoning_decision_refs':['r']};self.assertEqual(inspect_legacy_v1(v).document_id,'d')
 def test_migration_blocked(self):
  with self.assertRaises(GameContractError):migrate_legacy_v1({})
 def test_receipt(self):
  r=make_receipt('BIE-GAME-DSL-001',{'a':1},{'b':2},'impl');self.assertFalse(r.product_accepted)
 def test_receipt_stable(self):self.assertEqual(make_receipt('BIE-GAME-DSL-001',1,2,3),make_receipt('BIE-GAME-DSL-001',1,2,3))
