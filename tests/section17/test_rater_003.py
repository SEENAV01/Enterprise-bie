import unittest
from copy import deepcopy
from batch005_helpers import judgement_fixture,trust,token,NOW,TEST_KEY
from bie.evaluation.benchmarks.models import BenchmarkError,digest
from bie.evaluation.benchmarks.release import human,auth
class HumanRater003(unittest.TestCase):
    def setUp(self):
        self.ctx,self.rubric,self.ref,self.c,self.units=judgement_fixture();self.trust=trust()
        self.a=human.assignment(self.ctx,self.rubric,reviewer_id='reviewer',candidate_author_id='candidate-author')
        self.t=token('HUMAN_REVIEW',self.a['assignment_sha256'],{'units':self.units,'conflicts_declared':False})
    def execute(self,**kw):
        return human.execute(self.ctx,self.rubric,self.t,trust=self.trust,authenticated_subject=kw.pop('subject','reviewer'),candidate_author_id=kw.pop('author','candidate-author'),now=kw.pop('now',NOW),**kw)
    def resign(self):self.t=auth.sign(self.t['payload'],TEST_KEY)
    def test_signed_review_accepts_scoped_judgement(self):self.assertEqual('1',self.execute()['score_exact'])
    def test_fixture_review_never_live_human_claim(self):self.assertEqual('FIXTURE',self.execute()['execution']);self.assertFalse(self.execute()['evidence']['reviewer_expertise_independently_verified'])
    def test_unsigned_score_tampering_rejected(self):
        self.t['payload']['claims']['units'][0]['credit']='0'
        with self.assertRaisesRegex(BenchmarkError,'BAD_ATTESTATION_SIGNATURE'):self.execute()
    def test_wrong_key_rejected(self):
        self.trust['test-key']['secret']=b'x'*32
        with self.assertRaisesRegex(BenchmarkError,'BAD_ATTESTATION_SIGNATURE'):self.execute()
    def test_revoked_key_rejected(self):
        self.trust['test-key']['revoked']=True
        with self.assertRaisesRegex(BenchmarkError,'UNAUTHORIZED_ATTESTOR'):self.execute()
    def test_unknown_key_rejected(self):
        self.trust={}
        with self.assertRaisesRegex(BenchmarkError,'UNKNOWN_ATTESTATION_KEY'):self.execute()
    def test_wrong_authenticated_identity_rejected(self):
        with self.assertRaises(BenchmarkError):self.execute(subject='somebody-else')
    def test_author_cannot_review_self(self):
        with self.assertRaisesRegex(BenchmarkError,'CONFLICT_OF_INTEREST'):self.execute(author='reviewer')
    def test_rubric_owner_cannot_review_self(self):
        with self.assertRaisesRegex(BenchmarkError,'CONFLICT_OF_INTEREST'):human.assignment(self.ctx,self.rubric,reviewer_id='author',candidate_author_id='different-author')
    def test_declared_conflict_blocks(self):
        self.t['payload']['claims']['conflicts_declared']=True;self.resign()
        with self.assertRaisesRegex(BenchmarkError,'DECLARED_CONFLICT'):self.execute()
    def test_expiry_boundary_rejects(self):
        with self.assertRaisesRegex(BenchmarkError,'EXPIRED_OR_FUTURE'):self.execute(now=2000)
    def test_future_issue_rejects(self):
        with self.assertRaisesRegex(BenchmarkError,'EXPIRED_OR_FUTURE'):self.execute(now=899)
    def test_token_cannot_outlive_key(self):
        self.trust['test-key']['expires_at']=1500
        with self.assertRaisesRegex(BenchmarkError,'EXPIRED_OR_FUTURE'):self.execute()
    def test_review_other_candidate_rejects(self):
        self.ctx['candidate_sha256']=digest('other-candidate')
        with self.assertRaisesRegex(BenchmarkError,'SCOPE_MISMATCH'):self.execute()
    def test_missing_review_unit_rejects(self):
        self.t['payload']['claims']['units'].pop();self.resign()
        with self.assertRaisesRegex(BenchmarkError,'INCOMPLETE_JUDGEMENT'):self.execute()
    def test_partial_credit_exact(self):
        self.t['payload']['claims']['units'][1]['credit']='0';self.resign();self.assertEqual('3/4',self.execute()['score_exact'])
    def test_wrong_review_role_rejects(self):
        self.trust['test-key']['roles']=['POLICY_APPROVAL']
        with self.assertRaisesRegex(BenchmarkError,'UNAUTHORIZED_ATTESTOR'):self.execute()
    def test_fixture_key_cannot_authorize_production(self):
        with self.assertRaisesRegex(BenchmarkError,'FIXTURE_KEY_NOT_PRODUCTION'):self.execute(production=True)
    def test_wrong_scope_even_valid_signature_rejects(self):
        self.t['payload']['scope_sha256']='0'*64;self.resign()
        with self.assertRaisesRegex(BenchmarkError,'SCOPE_MISMATCH'):self.execute()
    def test_weak_key_rejected(self):
        with self.assertRaisesRegex(BenchmarkError,'WEAK_ATTESTATION_KEY'):auth.sign(self.t['payload'],b'weak')
    def test_ttl_resource_limit(self):
        self.t['payload']['expires_at']=999999
        with self.assertRaisesRegex(BenchmarkError,'INVALID_ATTESTATION_TTL'):self.resign()
    def test_false_like_string_not_conflict_false(self):
        self.t['payload']['claims']['conflicts_declared']='false';self.resign()
        with self.assertRaises(BenchmarkError):self.execute()
