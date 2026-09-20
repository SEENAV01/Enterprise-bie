import unittest
from bie.visual_intelligence.representation_core import *
from bie.visual_intelligence.rep004_map import *
def I(**kw):
 d=dict(intent_id='i',domain='geography',concept_ids=('c',),evidence_refs=('e',),reasoning_refs=('r',),semantic_tags=());d.update(kw);return SemanticIntent(**d)
class T(unittest.TestCase):
 def test_none(self):self.assertEqual(choose(I()).status,'UNSUPPORTED')
 def test_spatial(self):self.assertEqual(choose(I(spatial=True),has_region_membership=True).selected,'map')
 def test_crs(self):self.assertEqual(choose(I(),has_geographic_coordinates=True,crs='EPSG:4326').status,'PASS')
 def test_nocrs(self):self.assertEqual(choose(I(),has_geographic_coordinates=True).status,'BLOCKED')
 def test_route(self):self.assertEqual(choose(I(),has_route=True).selected,'map')
 def test_region(self):self.assertEqual(choose(I(),has_region_membership=True).selected,'map')
 def test_abstract(self):self.assertEqual(choose(I(spatial=True),spatial_relation_only=True).selected,'diagram')
 def test_uncert(self):self.assertLess(choose(I(spatial=True,uncertainty=.5),has_route=True).confidence,.92)
 def test_ground(self):self.assertEqual(choose(I(spatial=True),has_route=True).reasoning_refs,('r',))
 def test_accept(self):self.assertFalse(choose(I(spatial=True),has_route=True).accepted)
