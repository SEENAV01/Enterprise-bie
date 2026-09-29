from h8_helpers import *
import h8_helpers
sys.path.insert(0,str(ROOT/'tests/qa_publication22'))
from pub22_support import Fixture,NOW as PN

class Publication(Temp):
    def setUp(self):
        super().setUp();self.oldnow=h8_helpers.NOW;h8_helpers.NOW=PN
        self.f=Fixture(self.root/'candidate');self.cert=self.f.issue();self.approvals=self.f.approvals()
        self.store=PublicationStore(self.root/'store',create=True);self.wrapper=AttestedPublication(self.store)
        c=self.f.request.bundle.candidate;self.b=Binding(c.run_id,c.revision,c.content_digest,self.f.policy.content_digest)
        self.s=self.fresh(binding=self.b);self.k.establish(self.s,utc_ms=PN*1000)
    def tearDown(self):h8_helpers.NOW=self.oldnow;super().tearDown()
    def envelopes(self,operation):
        if operation=='publish':subject=digest({'request_digest':self.f.request.content_digest,'certificate_digest':digest(self.cert),'operation':'publish'})
        else:subject=digest({'request_digest':self.f.request.content_digest,'release_id':self.f.request.release_id,'artifact_id':'source','operation':'serve'})
        return self.k.roles(self.s,subject)
    def publish(self,**kw):
        opts=dict(session=self.s,envelopes=self.envelopes('publish'),verifier=self.f.verifier);opts.update(kw)
        return self.wrapper.publish(self.f.request,self.f.root,self.f.policy,self.approvals,self.f.authorities,self.f.journal,self.cert,**opts)
    def serve(self,**kw):
        opts=dict(session=self.s,envelopes=self.envelopes('serve'),verifier=self.f.verifier);opts.update(kw)
        return self.wrapper.serve(self.f.request.release_id,'source',self.f.request,self.f.policy,self.approvals,self.f.authorities,self.f.journal,**opts)
    def test_existing_certificate_verifier_still_executes(self):
        r=self.publish();self.assertFalse(r['production_authorized']);self.assertEqual(self.serve(),b'SYNTHETIC original; not a textbook')
    def test_missing_public_attestations(self):self.error('H8_ROLE_CENSUS',self.publish,envelopes=())
    def test_invalid_existing_certificate_not_overridden(self):
        self.cert={**self.cert,'signature':'0'*64};self.error('CERTIFICATE_SIGNATURE',self.publish)
    def test_revocation_blocks_serving(self):
        self.publish();self.f.journal.revoke(self.cert,reason='SYNTHETIC',as_of=PN);self.error('CERTIFICATE_REVOKED',self.serve)
    def test_wrong_candidate_binding(self):
        self.s=self.fresh(binding=replace(self.b,candidate_digest='0'*64));self.k.establish(self.s,utc_ms=PN*1000)
        self.error('H8_PUBLICATION_BINDING',self.publish)
    def test_wrong_policy_binding(self):
        self.s=self.fresh(binding=replace(self.b,policy_digest='0'*64));self.k.establish(self.s,utc_ms=PN*1000)
        self.error('H8_PUBLICATION_BINDING',self.publish)
    def test_serve_requires_own_operation_approval(self):
        self.publish();self.error('H8_STATEMENT_SCOPE',self.serve,envelopes=self.envelopes('publish'))
    def test_session_timeout_blocks_serving(self):
        self.publish();self.clock[0]=31_000_000_000;self.error('H8_SESSION_EXPIRED',self.serve)
    def test_reopen_with_same_verifier(self):
        self.publish();self.wrapper=AttestedPublication(PublicationStore(self.root/'store'));self.assertTrue(self.serve())
    def test_cannot_skip_legacy_approvals(self):
        self.approvals=()
        with self.assertRaises(ContractError):self.publish()
