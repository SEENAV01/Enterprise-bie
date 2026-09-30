from batch002_helpers import Batch002Base, attach_fixture_tests, q, date
from copy import deepcopy
from fractions import Fraction

@attach_fixture_tests
class HIST002Tests(Batch002Base):
    task="BIE-EVAL-HIST-002"

    def graph_link(self,a,b,y1,y2,eid):
        d=self.input();d.pop('op');d['cause']={'id':a,'date':date(y1)};d['effect']={'id':b,'date':date(y2)};d['evidence']=[{'id':eid,'cause_id':a,'effect_id':b,'kind':'source_interpretation','source_ref':'synthetic-annotation'}];d['alternatives_considered']=['alternative-Z'];return d
    def test_cycle_detected_without_proving_causation(self):
        d={'op':'audit_graph','links':[self.graph_link('A','B',1800,1801,'e1'),self.graph_link('B','A',1801,1800,'e2')]};v=self.values(d);self.assertTrue(v['cycle_detected']);self.assertTrue(v['review_required']);self.assertFalse(v['causality_proven'])
    def test_graph_permutation_deterministic(self):
        d={'op':'audit_graph','links':[self.graph_link('A','B',1800,1801,'e1'),self.graph_link('B','C',1801,1802,'e2')]};v=self.values(d);d['links'].reverse();self.assertEqual(v,self.values(d));self.assertFalse(v['cycle_detected'])
    def test_conflicting_node_dates_refused(self):
        d={'op':'audit_graph','links':[self.graph_link('A','B',1800,1801,'e1'),self.graph_link('B','C',1803,1804,'e2')]};self.rejected(d,'CONFLICTING_EVENT_DATES')
    def test_duplicate_edge_refused(self):
        l=self.graph_link('A','B',1800,1801,'e1');self.rejected({'op':'audit_graph','links':[l,deepcopy(l)]},'DUPLICATE_CAUSAL_EDGE')
    def test_self_causation_refused(self):
        d=self.input();d['effect']['id']=d['cause']['id'];self.rejected(d,'SELF_CAUSATION')
    def test_endpoint_not_an_alternative(self):
        d=self.input();d['alternatives_considered']=[d['cause']['id']];self.rejected(d,'ALTERNATIVE_REPEATS_ENDPOINT')
    def test_duplicate_alternatives_refused(self):
        d=self.input();d['alternatives_considered']=['A','A'];self.rejected(d,'DUPLICATE_ID')
    def test_unverified_annotation_never_becomes_source_verification(self):
        d=self.input();d['evidence'][0]['source_ref']='unverified-user-annotation';v=self.values(d);self.assertFalse(v['annotations_independently_verified']);self.assertFalse(v['causality_proven'])
    def test_unknown_evidence_kind_refused(self):
        d=self.input();d['evidence'][0]['kind']='verified_by_my_score';self.rejected(d,'UNSUPPORTED_ENUM')
    def test_same_day_does_not_imply_prior_cause(self):
        d=self.input();d['cause']['date']=date(1800,1,1);d['effect']['date']=date(1800,1,1);self.assertIn('TIME_ORDER_UNRESOLVED',self.values(d)['issues'])
