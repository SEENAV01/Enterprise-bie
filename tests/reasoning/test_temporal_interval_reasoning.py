import unittest
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.chronology_reasoning import TimeSpan
from bie.reasoning.temporal_interval_reasoning import TemporalInterval, interval_relation, interval_matrix
class Tests(unittest.TestCase):
 def setUp(self): self.refs=(EvidenceRef('s:1','primary',.9),)
 def t(self,a,b): return TimeSpan(a,b)
 def i(self,k,a,b): return TemporalInterval(k,k,self.t(a,b),('s:1',))
 def test_relations(self):
  cases=[((1,2),(3,4),'before'),((1,2),(2,4),'meets'),((1,3),(2,4),'overlaps'),((1,3),(1,4),'starts'),((2,3),(1,4),'during'),((2,4),(1,4),'finishes'),((1,4),(1,4),'equal'),((3,4),(1,2),'after')]
  for a,b,r in cases:self.assertEqual(interval_relation(self.t(*a),self.t(*b)),r)
 def test_inverse(self): self.assertEqual(interval_relation(self.t(2,4),self.t(1,3)),'overlapped_by')
 def test_matrix_grounded(self): self.assertEqual(interval_matrix([self.i('A',1,2),self.i('B',3,4)],self.refs).value['relations'][0]['evidence_ids'],['s:1'])
 def test_open_refused(self):
  with self.assertRaises(ValueError): interval_relation(TimeSpan(None,2),self.t(3,4))
 def test_axis_refused(self):
  with self.assertRaises(ValueError): interval_relation(self.t(1,2),TimeSpan(1,2,'gregorian_day'))
