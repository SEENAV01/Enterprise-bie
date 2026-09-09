
import unittest
from enterprise.alert_contracts import *
class T(unittest.TestCase):
 def r(self,**k):
  d=dict(rule_id="r",metric="queue_age",operator=">",threshold=10,severity="ERROR",window_seconds=60);d.update(k);return AlertRule(**d)
 def test_true(self): self.assertTrue(evaluate(self.r(),11))
 def test_false(self): self.assertFalse(evaluate(self.r(),9))
 def test_ge(self): self.assertTrue(evaluate(self.r(operator=">="),10))
 def test_bad_op(self):
  with self.assertRaises(AlertError): evaluate(self.r(operator="!="),1)
 def test_window(self):
  with self.assertRaises(AlertError): evaluate(self.r(window_seconds=0),1)
 def test_severity(self):
  with self.assertRaises(AlertError): evaluate(self.r(severity="INFO"),1)
if __name__=="__main__": unittest.main()
