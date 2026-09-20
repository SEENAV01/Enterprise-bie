import unittest
from bie.visual_intelligence.rights_metadata import *
class T(unittest.TestCase):
 def test_owned(self):self.assertTrue(validate_rights_for_production(RightsMetadata("r","owned",None,False,None,None,True,True,{}))[0])
 def test_unknown(self):self.assertFalse(validate_rights_for_production(RightsMetadata("r","unknown",None,False,None,None,None,None,{}))[0])
 def test_restricted(self):self.assertIn("rights_status=restricted",validate_rights_for_production(RightsMetadata("r","restricted",None,False,None,None,None,None,{}))[1])
 def test_commercial(self):self.assertFalse(RightsMetadata("r","licensed","x",False,None,None,False,True,{}).production_usable)
 def test_attr(self):
  with self.assertRaises(AssetRightsError):RightsMetadata("r","licensed","x",True,None,None,True,True,{})
 def test_bad(self):
  with self.assertRaises(AssetRightsError):RightsMetadata("r","magic",None,False,None,None,True,True,{})
 def test_public(self):self.assertTrue(RightsMetadata("r","public_domain",None,False,None,None,True,True,{}).production_usable)
