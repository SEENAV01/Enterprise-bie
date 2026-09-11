import unittest
from bie.reasoning.temporal_query_plan import *
class T(unittest.TestCase):
 def test_order(self): self.assertEqual(plan_temporal_query(TemporalQuery("before")),("ORDER",))
 def test_interval(self): self.assertEqual(plan_temporal_query(TemporalQuery("during")),("INTERVAL",))
 def test_extras(self): self.assertEqual(plan_temporal_query(TemporalQuery("duration",True,True)),("DURATION","UNCERTAINTY","PROVENANCE"))
 def test_unknown(self): self.assertEqual(plan_temporal_query(TemporalQuery("teleports")),("ABSTAIN_UNSUPPORTED_RELATION",))
