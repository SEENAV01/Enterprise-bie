
import unittest
from enterprise.feature_flags import *
class T(unittest.TestCase):
 def test_enabled(self):
  f=FeatureFlags([FeatureFlag("x",True,"test","infra")]); self.assertTrue(f.enabled("x"))
 def test_disabled(self):
  f=FeatureFlags([FeatureFlag("x",False,"test","infra")]); self.assertFalse(f.enabled("x"))
 def test_default(self): self.assertTrue(FeatureFlags().enabled("x",True))
 def test_duplicate(self):
  f=FeatureFlags([FeatureFlag("x",True,"r","o")])
  with self.assertRaises(FeatureFlagError): f.set(FeatureFlag("x",False,"r2","o"))
 def test_required_name(self):
  with self.assertRaises(FeatureFlagError): FeatureFlags([FeatureFlag("",True,"r","o")])
 def test_snapshot_sorted(self):
  f=FeatureFlags([FeatureFlag("b",True,"r","o"),FeatureFlag("a",False,"r","o")]); self.assertEqual(list(f.snapshot()),["a","b"])
if __name__=="__main__": unittest.main()
