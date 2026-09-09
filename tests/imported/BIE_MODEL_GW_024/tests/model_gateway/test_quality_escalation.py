
import unittest
from bie.model_gateway.quality_escalation import *
class T(unittest.TestCase):
 def p(self):return QualityPolicy(.8,2)
 def test_accept(self):self.assertEqual(next_action(.9,0,self.p()),"ACCEPT")
 def test_escalate(self):self.assertEqual(next_action(.5,0,self.p()),"ESCALATE")
 def test_review(self):self.assertEqual(next_action(.5,2,self.p()),"REVIEW")
 def test_bad(self):
  with self.assertRaises(EscalationError):next_action(2,0,self.p())
 def test_threshold(self):self.assertEqual(next_action(.8,0,self.p()),"ACCEPT")
if __name__=="__main__":unittest.main()
