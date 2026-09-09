
import unittest
from enterprise.disaster_recovery import *
class T(unittest.TestCase):
 def p(self,**k):
  d=dict(rpo_minutes=15,rto_minutes=60,backup_interval_minutes=10,multi_zone=True,drill_interval_days=30);d.update(k);return DRPolicy(**d)
 def test_ok(self):self.assertTrue(validate(self.p()))
 def test_rpo(self):
  with self.assertRaises(DRError):validate(self.p(backup_interval_minutes=20))
 def test_zone(self):
  with self.assertRaises(DRError):validate(self.p(multi_zone=False))
 def test_drill(self):
  with self.assertRaises(DRError):validate(self.p(drill_interval_days=0))
 def test_sequence(self):self.assertEqual(recovery_sequence()[0],"declare_incident")
 def test_release_last(self):self.assertEqual(recovery_sequence()[-1],"release_health_check")
if __name__=="__main__":unittest.main()
