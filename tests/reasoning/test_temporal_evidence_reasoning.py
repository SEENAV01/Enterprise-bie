import unittest
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.chronology_reasoning import TimeSpan
from bie.reasoning.temporal_evidence_reasoning import TemporalHypothesis,fuse_temporal_hypotheses
class Tests(unittest.TestCase):
 def setUp(self): self.refs=(EvidenceRef('e1','primary',.9),EvidenceRef('e2','supporting',.8))
 def h(self,k,a,b,e): return TemporalHypothesis(k,TimeSpan(a,b),(e,))
 def test_consensus(self):
  r=fuse_temporal_hypotheses('X',[self.h('A',1,5,'e1'),self.h('B',3,7,'e2')],self.refs);self.assertEqual(r.value['consensus']['earliest'],3);self.assertEqual(r.value['consensus']['latest'],5)
 def test_conflict(self):
  r=fuse_temporal_hypotheses('X',[self.h('A',1,2,'e1'),self.h('B',3,4,'e2')],self.refs);self.assertEqual(r.status,'CONFLICT');self.assertEqual(r.value['conflicting_pairs'],[['A','B']])
 def test_no_authority_invention(self): self.assertIn('source authority is not invented',fuse_temporal_hypotheses('X',[self.h('A',1,2,'e1')],self.refs).assumptions[0])
 def test_axis_refused(self):
  with self.assertRaises(ValueError):fuse_temporal_hypotheses('X',[self.h('A',1,2,'e1'),TemporalHypothesis('B',TimeSpan(1,2,'gregorian_day'),('e2',))],self.refs)
 def test_open_refused(self):
  with self.assertRaises(ValueError):fuse_temporal_hypotheses('X',[TemporalHypothesis('A',TimeSpan(None,2),('e1',))],self.refs)
