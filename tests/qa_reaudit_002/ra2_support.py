"""All authorities below are synthetic, ephemeral test fixtures."""
from pathlib import Path
from dataclasses import replace
import sys,tempfile,unittest,sqlite3,json
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
for name in ('qa_hardening_h8','qa_publication22','qa_performance21'):
    sys.path.insert(0,str(ROOT/'tests'/name))
import h8_helpers as h
from pub22_support import Fixture,NOW
from bie.qa.assurance_quality_v2.authority import (
 AuthoritySession,AuthorityJournal,TrustPolicy,AttestedPublication)
from bie.qa.assurance_quality_v2.common import Binding,ContractError,digest
from bie.qa.operational_quality_v2.publication import PublicationStore

class PubCase(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.clock=[0];old=h.NOW;h.NOW=NOW
        self.addCleanup(setattr,h,'NOW',old)
        self.k=h.Keys();self.f=Fixture(self.root/'candidate');self.cert=self.f.issue()
        self.approvals=self.f.approvals();self.store=PublicationStore(self.root/'store',create=True)
        self.wrapper=AttestedPublication(self.store);c=self.f.request.bundle.candidate
        self.binding=Binding(c.run_id,c.revision,c.content_digest,self.f.policy.content_digest)
        self.journal=AuthorityJournal(self.root/'authority',create=True)
        self.session=AuthoritySession(self.k.policy(),self.binding,self.journal,
                                      monotonic_ns=lambda:self.clock[0])
        self.k.establish(self.session,utc_ms=NOW*1000)
    def roles(self,operation,expires=NOW+120):
        fields={'request_digest':self.f.request.content_digest,'operation':operation}
        if operation=='publish':fields['certificate_digest']=digest(self.cert)
        else:fields.update(release_id=self.f.request.release_id,artifact_id='source')
        subject=digest(fields)
        return tuple(self.k.envelope(self.session,p,subject,
          {'decision':'APPROVE','trust_digest':self.session.policy.content_digest},expires=expires)
          for p in ('capture','review','issuer'))
    def publish(self,envelopes=None):
        f=self.f
        return self.wrapper.publish(f.request,f.root,f.policy,self.approvals,f.authorities,
            f.journal,self.cert,session=self.session,envelopes=envelopes or self.roles('publish'),verifier=f.verifier)
    def serve(self,envelopes=None):
        f=self.f
        return self.wrapper.serve(f.request.release_id,'source',f.request,f.policy,self.approvals,
            f.authorities,f.journal,session=self.session,envelopes=envelopes or self.roles('serve'),verifier=f.verifier)
    def error(self,code,fn,*args,**kw):
        with self.assertRaises(ContractError) as cm:fn(*args,**kw)
        self.assertIn(code,str(cm.exception))
    def empty_active(self):
        with sqlite3.connect(self.store.db) as c:
            for table in ('active','releases','audit'):
                self.assertEqual(c.execute('select count(*) from '+table).fetchone()[0],0)
    def raw_publish(self,guard=None,policy=None):
        f=self.f
        return self.store.publish(f.request,f.root,policy or f.policy,self.approvals,f.authorities,
            f.journal,self.cert,now=NOW,verifier=f.verifier,authorization_guard=guard)
