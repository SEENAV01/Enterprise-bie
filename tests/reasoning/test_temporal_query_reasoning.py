import unittest
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.temporal_constraint_reasoning import TemporalConstraint
from bie.reasoning.temporal_query_reasoning import explain_before
class Tests(unittest.TestCase):
 def setUp(self): self.refs=(EvidenceRef('e1','primary',.9),EvidenceRef('e2','supporting',.8))
 def c(self,a,b,e='e1'): return TemporalConstraint(a,b,(e,))
 def test_forward(self):
  r=explain_before('ABC',[self.c('A','B'),self.c('B','C','e2')],'A','C',self.refs);self.assertEqual(r.value['relation'],'before');self.assertEqual(r.value['witness_path'],['A','B','C']);self.assertEqual(r.value['witness_evidence_ids'],['e1','e2'])
 def test_reverse(self): self.assertEqual(explain_before('AB',[self.c('A','B')],'B','A',self.refs).value['relation'],'after')
 def test_indeterminate(self): self.assertEqual(explain_before('ABC',[self.c('A','B')],'A','C',self.refs).status,'AMBIGUOUS')
 def test_cycle_conflict(self): self.assertEqual(explain_before('AB',[self.c('A','B'),self.c('B','A')],'A','B',self.refs).status,'CONFLICT')
 def test_unknown_endpoint(self):
  with self.assertRaises(ValueError):explain_before('AB',[self.c('A','B')],'A','Z',self.refs)
