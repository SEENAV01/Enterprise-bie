import unittest
from bie.reasoning.temporal_provenance_merge import *
class T(unittest.TestCase):
 def test_merge(self):
  r=merge_temporal_evidence([TemporalEvidence("b","A before B",.7),TemporalEvidence("a","A before B",.8)])
  self.assertEqual(r.source_ids,("a","b")); self.assertEqual(r.confidence,.8)
 def test_empty(self):
  with self.assertRaises(ValueError): merge_temporal_evidence([])
 def test_conflict(self):
  with self.assertRaises(ValueError): merge_temporal_evidence([TemporalEvidence("a","x",.5),TemporalEvidence("b","y",.5)])
 def test_bad_conf(self):
  with self.assertRaises(ValueError): merge_temporal_evidence([TemporalEvidence("a","x",1.2)])
