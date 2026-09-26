import unittest
from dataclasses import replace
from bie.game_engine.qa_engine.contracts import *
from bie.game_engine.qa_engine.policy import GameQAPolicy
from bie.game_engine.qa_engine.errors import GameQAError
class Tests(unittest.TestCase):
 def test_policy_valid(self):GameQAPolicy().validate()
 def test_policy_rejects_product_acceptance(self):
  with self.assertRaises(GameQAError):replace(GameQAPolicy(),product_accepted=True).validate()
 def test_blocking_warning_forbidden(self):
  with self.assertRaises(GameQAError):QualityFinding('f',Severity.WARNING,'CODE','msg',(),True).validate()
 def test_result_pass_with_blocker_rejected(self):
  f=QualityFinding('f',Severity.ERROR,'C','m',(),True)
  with self.assertRaises(GameQAError):QAGateResult('T',GateStatus.PASS,1,(),(f,),('e',),'sha256:'+'1'*64,'sha256:'+'2'*64).validate()
 def test_report_requires_ten(self):
  with self.assertRaises(GameQAError):GameQAReport((),'sha256:'+'1'*64,True).validate()
