import unittest
from app.bie.reasoning.escalation_policy import *
class T(unittest.TestCase):
 def test_specialist(self):self.assertEqual(escalate(.8,0,1,["specialist"]),"specialist")
 def test_conflict(self):self.assertEqual(escalate(.8,.8,0,["evidence_review"]),"evidence_review")
 def test_model(self):self.assertEqual(escalate(.2,0,0,["stronger_model"]),"stronger_model")
 def test_none(self):self.assertEqual(escalate(.9,0,0,[]),"none")
