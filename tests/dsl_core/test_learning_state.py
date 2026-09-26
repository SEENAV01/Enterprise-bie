import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.fixtures import evidence
from bie.game_engine.learning import LearningTarget
from bie.game_engine.state import *
from bie.game_engine.expressions import ValueType
class T(unittest.TestCase):
 def test_learning(self):LearningTarget('o',('c',),(),(),.8,evidence()).validate()
 def test_learning_no_concept(self):
  with self.assertRaises(GameContractError):LearningTarget('o',(),(),(),.8,evidence()).validate()
 def test_mastery_range(self):
  with self.assertRaises(GameContractError):LearningTarget('o',('c',),(),(),1.1,evidence()).validate()
 def test_state(self):StateVariableSpec('x',ValueType.NUMBER,1,0,2).validate()
 def test_state_range(self):
  with self.assertRaises(GameContractError):StateVariableSpec('x',ValueType.NUMBER,3,0,2).validate()
 def test_enum(self):StateVariableSpec('e',ValueType.ENUM,'a',enum_values=('a','b')).validate()
 def test_enum_bad(self):
  with self.assertRaises(GameContractError):StateVariableSpec('e',ValueType.ENUM,'c',enum_values=('a','b')).validate()
 def test_model_duplicate(self):
  v=StateVariableSpec('x',ValueType.NUMBER,1)
  with self.assertRaises(GameContractError):StateModel((v,v)).validate()
