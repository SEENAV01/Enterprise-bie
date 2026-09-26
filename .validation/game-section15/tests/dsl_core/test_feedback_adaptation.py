import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.feedback import *
from bie.game_engine.adaptation import *
from bie.game_engine.state import *
from bie.game_engine.expressions import *
class T(unittest.TestCase):
 def state(self):return StateModel((StateVariableSpec('x',ValueType.NUMBER,1),)).validate()
 def test_feedback(self):FeedbackContract('s','f',(('m','r'),),None,False).validate()
 def test_answer_reveal(self):
  with self.assertRaises(GameContractError):FeedbackContract('s','f',(),None,True).validate()
 def test_adapt(self):AdaptationRule('a',Compare(CompareOp.GT,Variable('x'),Literal(1)),AdaptAction.ADVANCE,1).validate(self.state())
 def test_adapt_target(self):
  with self.assertRaises(GameContractError):AdaptationRule('a',Literal(True),AdaptAction.REMEDIATE,1).validate(self.state())
 def test_priority_tie(self):
  a=AdaptationRule('a',Literal(True),AdaptAction.ADVANCE,1);b=AdaptationRule('b',Literal(True),AdaptAction.REPEAT,1)
  with self.assertRaises(GameContractError):AdaptationContract((a,b)).validate(self.state())
