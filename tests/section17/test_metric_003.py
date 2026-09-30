from batch003_helpers import MetricBase,attach_metric_fixtures
@attach_metric_fixtures
class METRIC003Tests(MetricBase):
    task='BIE-EVAL-METRIC-003'
    def test_known_prior_removes_reteaching_requirement(self):
        r,c,a=self.example();r['payload']['known_prior']=['charge'];c['teaching_order']=['vector','force'];self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_all_targets_known_cannot_vacuously_pass(self):
        r,c,a=self.example();r['payload']['known_prior']=['force'];self.reject(r,c,a,code='NO_UNMASTERED_TARGET_IN_PROFILE')
    def test_reference_cycle_blocked(self):
        r,c,a=self.example();r['payload']['edges'].append({'id':'back','weight':1,'prerequisite':'force','dependent':'charge'});self.reject(r,c,a,code='CYCLIC_REFERENCE_GRAPH')
    def test_duplicate_teaching_node_rejected(self):
        r,c,a=self.example();c['teaching_order'].append('force');self.reject(r,c,a,code='DUPLICATE_METRIC_ITEM')
    def test_unknown_teaching_node_rejected(self):
        r,c,a=self.example();c['teaching_order'].append('fabricated');self.reject(r,c,a,code='UNKNOWN_CANDIDATE_NODE')
    def test_transitive_prerequisite_must_be_taught(self):
        r,c,a=self.example();r['payload']['nodes'].append('notation');r['payload']['edges'].append({'id':'nq','weight':1,'prerequisite':'notation','dependent':'charge'});v=self.measure(r,c,a);self.assertIn('notation',v['details']['required_nodes']);self.assertEqual('FAIL',v['outcome'])
    def test_disconnected_nonrequired_node_not_penalized(self):
        r,c,a=self.example();r['payload']['nodes'].append('unrelated');self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_known_prior_cuts_ancestor_reteaching(self):
        r,c,a=self.example();r['payload']['nodes'].append('notation');r['payload']['edges'].append({'id':'nq','weight':1,'prerequisite':'notation','dependent':'charge'});r['payload']['known_prior']=['charge'];c['teaching_order']=['vector','force'];v=self.measure(r,c,a);self.assertNotIn('notation',v['details']['required_nodes']);self.assertEqual('PASS',v['outcome'])
    def test_reference_unknown_target_rejected(self):
        r,c,a=self.example();r['payload']['targets']=['absent'];self.reject(r,c,a,code='UNKNOWN_REFERENCE_NODE')
    def test_duplicate_reference_edge_rejected(self):
        r,c,a=self.example();r['payload']['edges'].append({'id':'copy','weight':1,'prerequisite':'charge','dependent':'force'});self.reject(r,c,a,code='DUPLICATE_GRAPH_EDGE')
    def test_independent_prerequisites_can_swap(self):
        r,c,a=self.example();c['teaching_order']=['vector','charge','force'];self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_prior_knowledge_is_not_candidate_owned(self):
        r,c,a=self.example();c['known_prior']=['force'];self.reject(r,c,a)
