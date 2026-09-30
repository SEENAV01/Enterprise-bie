from batch003_helpers import MetricBase,attach_metric_fixtures
from copy import deepcopy
from bie.evaluation.benchmarks.metrics.grounding import text_sha
@attach_metric_fixtures
class METRIC001Tests(MetricBase):
    task='BIE-EVAL-METRIC-001'
    def test_source_tamper_blocked(self):
        r,c,a=self.example();a['doc']+=' changed';self.reject(r,c,a,code='SOURCE_ARTIFACT_HASH_MISMATCH')
    def test_missing_source_artifact_blocked(self):self.reject(artifacts={},code='SOURCE_ARTIFACT_ROSTER_MISMATCH')
    def test_reference_span_tamper_blocked(self):
        r,c,a=self.example();r['payload']['claims'][0]['supports'][0]['span_sha256']='0'*64;self.reject(r,c,a,code='REFERENCE_SPAN_HASH_MISMATCH')
    def test_negative_span_rejected(self):
        r,c,a=self.example();c['claims'][0]['citations'][0]['start']=-1;self.reject(r,c,a,code='INVALID_SOURCE_SPAN')
    def test_boolean_span_not_an_index(self):
        r,c,a=self.example();c['claims'][0]['citations'][0]['start']=False;self.reject(r,c,a,code='INVALID_SOURCE_SPAN')
    def test_duplicate_citation_not_double_credit(self):
        r,c,a=self.example();c['claims'][0]['citations']*=2;self.reject(r,c,a,code='DUPLICATE_CITATION')
    def test_unknown_source_rejected(self):
        r,c,a=self.example();c['claims'][0]['citations'][0]['source_id']='unknown';self.reject(r,c,a,code='UNKNOWN_SOURCE')
    def test_extra_claim_does_not_expand_denominator(self):
        r,c,a=self.example();extra=deepcopy(c['claims'][0]);extra['id']='invented';c['claims'].append(extra);self.reject(r,c,a,code='UNEXPECTED_METRIC_ITEM')
    def test_empty_reference_never_perfect(self):
        r,c,a=self.example();r['payload']['claims']=[];self.reject(r,c,a)
    def test_unicode_offsets_are_codepoints_not_bytes(self):
        r,c,a=self.example();prefix='कक्षा α ';a['doc']=prefix+a['doc'];r['payload']['sources'][0]['text_sha256']=text_sha(a['doc'])
        for row in r['payload']['claims']:
            for span in row['supports']:span['start']+=len(prefix);span['end']+=len(prefix)
        for row in c['claims']:
            for span in row['citations']:span['start']+=len(prefix);span['end']+=len(prefix)
        self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_one_correct_plus_one_wrong_citation_is_not_accepted(self):
        r,c,a=self.example();c['claims'][0]['citations'].append(deepcopy(c['claims'][1]['citations'][0]));self.assertEqual('1/3',self.measure(r,c,a)['score_exact'])
    def test_candidate_cannot_supply_its_own_weight(self):
        r,c,a=self.example();c['claims'][0]['weight']=1000000;self.reject(r,c,a)
    def test_reference_weight_sets_denominator(self):
        r,c,a=self.example(1);r['payload']['claims'][0]['weight']=9;self.assertEqual('1/10',self.measure(r,c,a)['score_exact'])
    def test_proposition_type_distinguishes_boolean_integer(self):
        r,c,a=self.example();r['payload']['claims'][0]['proposition']['object']=True;c['claims'][0]['proposition']['object']=1;self.assertIn('PROPOSITION_MISMATCH',self.reasons(self.measure(r,c,a)))
