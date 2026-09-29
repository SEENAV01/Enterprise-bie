"""SYNTHETIC operator inventories, credentials and receipt fixtures only."""
from pathlib import Path
import tempfile,unittest,json,hashlib,hmac,sys
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'qa_publication22'))
from pub22_support import Fixture,Case,ref,NOW
from bie.qa.release_v2.contracts import canonical_bytes,digest,ContractError
from bie.qa.governance_v2.contracts import *
from bie.qa.publication_v2.report_policy import TERMINAL_SCHEMA

class InventoryCase(Case):
    def raw(self):return json.loads((self.root/self.f.request.inventory.path).read_text())
    def mutate(self,fn):
        data=self.raw();fn(data)
        old=self.f.request.inventory;new=ref(self.root,old.artifact_id,old.path,data)
        self.f.request=replace(self.f.request,inventory=new)
    def need_gap(self):
        a=self.f.policy.inventory_authority
        o=Obligation('SYNTHETIC-GAP','QA.TEST','LOCAL',digest({'rule':'a visible tested obligation'}),('closure-check',),digest({'policy':'test'}),('source',),'DIAGNOSTIC')
        k=ClosureKey('test-closure','test-principal','test-group',b'SYNTHETIC-CLOSURE-SECRET-00000000000',(o.obligation_id,))
        self.f.policy=replace(self.f.policy,inventory_authority=replace(a,obligations=(o,),closure_keys=(k,)))
        self.o=o;self.k=k;self.f.refresh_inventory()
    def closed(self):
        a=self.f.policy.inventory_authority;c=self.f.request.bundle.candidate
        data=dict(schema_version=TERMINAL_SCHEMA,report_id='closure-evidence',status='PASS',scope='DIAGNOSTIC',binding=dict(
            subject_type='obligation',subject_id=self.o.obligation_id,evidence_id='closure',candidate_digest=c.content_digest,
            run_id=c.run_id,revision=c.revision,release_policy_digest=self.f.policy.release_policy.content_digest,
            evaluator_policy_digest=self.o.evaluator_policy_digest,bundle_digest=None,
            inspected_artifacts=[x.to_dict() for x in a.artifacts if x.artifact_id in self.o.affected_artifact_ids]),
            captured_at=NOW-10,created_at=NOW-10,expires_at=NOW+3600,
            checks=[dict(check_id='closure-check',status='PASS',diagnostics=[],checks=[])],diagnostics=[],ledgers=[],immutable_facts=[])
        er=ref(self.root,'closure-evidence','closure/evidence.json',data)
        raw=dict(schema_version=CLOSURE_SCHEMA,closure_id='closure',obligation_id=self.o.obligation_id,owner=self.o.owner,scope=self.o.scope,
            definition_digest=self.o.definition_digest,authority_digest=a.content_digest,candidate_digest=c.content_digest,run_id=c.run_id,revision=c.revision,
            evidence_scope='DIAGNOSTIC',status='CLOSED',created_at=NOW-5,expires_at=NOW+3600,evidence=[er.to_dict()],approvals=[])
        self.write_closure(raw)
    def closure(self):return json.loads((self.root/'closure/closure.json').read_text())
    def write_closure(self,raw,sign=True):
        if sign:raw['approvals']=[dict(key_id=self.k.key_id,principal_id=self.k.principal_id,purpose='gap_closure',signature=hmac.new(self.k.secret,closure_signing_bytes(raw),hashlib.sha256).hexdigest())]
        cr=ref(self.root,'closure','closure/closure.json',raw)
        self.mutate(lambda d:d['obligations'][0].update(status='CLOSED',closure_ref=cr.to_dict()))
    def mutate_closure(self,fn,sign=True):
        data=self.closure();fn(data);self.write_closure(data,sign)
    def mutate_evidence(self,fn):
        raw=json.loads((self.root/'closure/evidence.json').read_text());fn(raw)
        er=ref(self.root,'closure-evidence','closure/evidence.json',raw)
        self.mutate_closure(lambda d:d.update(evidence=[er.to_dict()]))

class GapCase(InventoryCase):
    def setUp(self):super().setUp();self.need_gap();self.closed()
