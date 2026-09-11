import unittest
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.temporal_constraint_reasoning import TemporalConstraint,constraint_closure
class Tests(unittest.TestCase):
 def setUp(self): self.refs=(EvidenceRef('e1','primary',.9),EvidenceRef('e2','supporting',.8))
 def c(self,a,b,e='e1'): return TemporalConstraint(a,b,(e,))
 def test_transitive(self):
  r=constraint_closure('ABC',[self.c('A','B'),self.c('B','C','e2')],self.refs); d=[x for x in r.value['closure'] if x['before']=='A' and x['after']=='C'][0];self.assertTrue(d['derived']);self.assertEqual(d['evidence_ids'],['e1','e2'])
 def test_cycle(self):
  r=constraint_closure('AB',[self.c('A','B'),self.c('B','A')],self.refs);self.assertEqual(r.status,'CONFLICT');self.assertTrue(r.value['contradiction_witness']['cycle'])
 def test_duplicate(self):
  with self.assertRaises(ValueError):constraint_closure('AB',[self.c('A','B'),self.c('A','B')],self.refs)
 def test_unknown(self):
  with self.assertRaises(ValueError):constraint_closure('AB',[self.c('A','Z')],self.refs)
 def test_deterministic(self):
  a=constraint_closure('ABC',[self.c('A','B'),self.c('B','C')],self.refs);b=constraint_closure('CBA',[self.c('B','C'),self.c('A','B')],self.refs);self.assertEqual(a.result_id,b.result_id)
