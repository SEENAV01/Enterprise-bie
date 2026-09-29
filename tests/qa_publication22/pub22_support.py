"""All keys, reports, approvals and media in this module are SYNTHETIC fixtures.
No proof of real rendering, real books, section exit or operational approval."""
import json,hashlib,hmac,tempfile,unittest
from pathlib import Path
from dataclasses import replace
from bie.qa.release_v2.contracts import *
from bie.qa.release_v2.policy import enterprise_policy
from bie.qa.release_v2.trust import TrustedKey,HmacEvidenceVerifier
from bie.qa.publication_v2 import *
from bie.qa.governance_v2.contracts import InventoryAuthority,INVENTORY_SCHEMA
from bie.qa.publication_v2.report_policy import TerminalRequirement, TERMINAL_SCHEMA
from bie.qa.publication_v2.contracts import SCHEMA,PROOF_SCHEMA,EXIT_SCHEMA,STAGES,PURPOSES

NOW=1790546400
REV='375d99af0edd0086206817dae932156ddf61c569'
def ref(root,aid,path,data,role='report'):
    b=data if isinstance(data,bytes) else canonical_bytes(data)
    p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    return ArtifactRef(aid,path,hashlib.sha256(b).hexdigest(),len(b),role)
def sign_ev(ev,key):return replace(ev,signature=hmac.new(key.secret,ev.signing_bytes(),hashlib.sha256).hexdigest())
def sign_approval(a,key):return replace(a,signature=hmac.new(key.secret,a.signing_bytes(),hashlib.sha256).hexdigest())

class Fixture:
    def __init__(self,root):
        self.root=root;self.policy=PublicationPolicy('SYNTHETIC-TEST-ENVIRONMENT')
        rp=self.policy.release_policy
        self.policy=replace(self.policy,terminal_requirements=tuple(
            TerminalRequirement(kind,subject,digest({'SYNTHETIC_EVALUATOR_POLICY':kind+':'+subject}),('synthetic-check',))
            for kind,subjects in (('gate',[g.gate_id for g in rp.gates]),('section_exit',STAGES)) for subject in subjects))
        artifacts=(ref(root,'source','subjects/source.txt',b'SYNTHETIC original; not a textbook','source'),
            ref(root,'video','subjects/video.fixture',b'SYNTHETIC; not video media','video'),
            ref(root,'game','subjects/game.fixture',b'SYNTHETIC; not a playable game','game'))
        cand=ReleaseCandidate('2.0.0','synthetic-candidate','synthetic-run',REV,artifacts)
        self.evkey=TrustedKey('synthetic-gate-key',b'fixture-evidence-secret-000000000000','synthetic-evaluator','1.0.0',tuple(g.gate_id for g in rp.gates),('execution','review'),'operator_managed')
        self.verifier=HmacEvidenceVerifier((self.evkey,));evs=[]
        self.native={}
        for g in rp.gates:
            native=ref(root,'native-'+g.gate_id,'native/'+g.gate_id+'.json',self.terminal(cand,'gate',g.gate_id,'ev-'+g.gate_id,tuple(a for a in artifacts if a.role in g.required_roles)))
            self.native[g.gate_id]=native
            raw=dict(schema_version=PROOF_SCHEMA,evidence_id='ev-'+g.gate_id,gate_id=g.gate_id,candidate_digest=cand.content_digest,
                policy_digest=rp.content_digest,run_id=cand.run_id,revision=cand.revision,status='PASS',scope='DIAGNOSTIC',
                checks=[dict(check_id='synthetic-check',status='PASS',diagnostics=[])],source_reports=[native.to_dict()])
            report=ref(root,'proof-'+g.gate_id,'proofs/'+g.gate_id+'.json',raw)
            ev=GateEvidence('2.0.0','ev-'+g.gate_id,g.gate_id,cand.content_digest,rp.content_digest,cand.run_id,cand.revision,'PASS',
                self.evkey.evaluator_id,self.evkey.evaluator_version,'execution',tuple(a.artifact_id for a in artifacts if a.role in g.required_roles),report,
                NOW-5,NOW+3600,(),self.evkey.key_id)
            evs.append(sign_ev(ev,self.evkey))
        bundle=EvidenceBundle('2.0.0',cand,tuple(evs))
        self.request=PublicationRequest(SCHEMA,'synthetic-release','0.0.1',bundle,(Lineage('video',('source',)),Lineage('game',('source',))))
        self.policy=replace(self.policy,inventory_authority=InventoryAuthority('SYNTHETIC-INVENTORY','1','DIAGNOSTIC',artifacts,('SYNTHETIC-TASK',),self.policy.terminal_requirements,(),catalog_digest=digest({'diagnostic_catalog':True})))
        self.refresh_governance()
        self.keys=tuple(AuthorityKey('test-'+p,'principal-'+p,(p+'-SYNTHETIC-SECRET').encode().ljust(48,b'0'),(p,)) for p in PURPOSES)+(
            AuthorityKey('test-issuer','principal-issuer',b'ISSUER-SYNTHETIC-SECRET-000000000000',('issuer',)),)
        self.authorities=AuthorityStore(self.keys)
        self.jdir=root/'private-journal';self.jdir.mkdir(mode=0o700)
        self.journal=ReleaseJournal(self.jdir/'publication.db')
    def terminal(self,c,kind,subject,evidence_id,artifacts,bundle_digest=None):
        requirement=next(r for r in self.policy.terminal_requirements if (r.subject_type,r.subject_id)==(kind,subject))
        return dict(schema_version=TERMINAL_SCHEMA,report_id=('native-'+subject if kind=='gate' else 'exit-native-'+subject),status='PASS',scope='DIAGNOSTIC',
            binding=dict(subject_type=kind,subject_id=subject,evidence_id=evidence_id,candidate_digest=c.content_digest,
                run_id=c.run_id,revision=c.revision,release_policy_digest=self.policy.release_policy.content_digest,
                evaluator_policy_digest=requirement.evaluator_policy_digest,bundle_digest=bundle_digest,
                inspected_artifacts=[a.to_dict() for a in sorted(artifacts,key=lambda a:a.artifact_id)]),
            captured_at=NOW-10,created_at=NOW-10,expires_at=NOW+3600,checks=[dict(check_id='synthetic-check',status='PASS',diagnostics=[],checks=[])],
            diagnostics=[],ledgers=[],immutable_facts=[])
    def refresh_governance(self):
        c=self.request.bundle.candidate;gov=[]
        for stage in STAGES:
            native=ref(self.root,'exit-native-'+stage,'native/exit-'+stage+'.json',self.terminal(c,'section_exit',stage,'exit-'+stage,c.artifacts,self.request.bundle.content_digest))
            gov.append(ref(self.root,'exit-'+stage,'exit/'+stage+'.json',dict(schema_version=EXIT_SCHEMA,stage=stage,status='PASS',revision=c.revision,
                candidate_digest=c.content_digest,bundle_digest=self.request.bundle.content_digest,open_must_have_ids=[],scope='DIAGNOSTIC',source_reports=[native.to_dict()])))
        self.request=replace(self.request,governance=tuple(gov))
        self.refresh_inventory()
    def refresh_inventory(self):
        # Explicit test-only operator census, fixed at Fixture construction. It is
        # not inferred again from a mutated candidate or accepted request JSON.
        a=self.policy.inventory_authority;c=self.request.bundle.candidate
        if a is None:return
        raw=dict(schema_version=INVENTORY_SCHEMA,authority_digest=a.content_digest,candidate_digest=c.content_digest,run_id=c.run_id,revision=c.revision,
            created_at=NOW-5,expires_at=NOW+3600,artifacts=[x.to_dict() for x in a.artifacts],task_ids=list(a.task_ids),
            checks=[dict(subject_type=x.subject_type,subject_id=x.subject_id,check_ids=list(x.required_check_ids)) for x in a.check_requirements],
            obligations=[dict(obligation_id=o.obligation_id,owner=o.owner,scope=o.scope,definition_digest=o.definition_digest,status='OPEN',closure_ref=None) for o in a.obligations])
        inv=ref(self.root,'inventory','inventory/census.json',raw)
        self.request=replace(self.request,inventory=inv)
    def assess(self,**kwargs):return assess(self.request,self.root,self.policy,as_of=kwargs.pop('as_of',NOW),verifier=kwargs.pop('verifier',self.verifier),**kwargs)
    def ev(self,gate='video_render'):return next(e for e in self.request.bundle.evidence if e.gate_id==gate)
    def update_ev(self,gate='video_render',resign=True,**changes):
        e=replace(self.ev(gate),**changes)
        if resign:e=sign_ev(e,self.evkey)
        self.request=replace(self.request,bundle=replace(self.request.bundle,evidence=tuple(e if x.gate_id==gate else x for x in self.request.bundle.evidence)))
        self.refresh_governance();return e
    def proof(self,mutate,gate='video_render'):
        e=self.ev(gate);d=json.loads((self.root/e.report.path).read_text());mutate(d)
        report=ref(self.root,e.report.artifact_id,e.report.path,d)
        self.update_ev(gate,report=report)
    def approvals(self,assessment=None):
        d=(assessment or self.assess()).content_digest
        return tuple(sign_approval(Approval('approval-'+p,p,k.principal_id,k.key_id,d,NOW-1,NOW+1800,'APPROVE'),k) for p,k in zip(PURPOSES,self.keys))
    def issue(self,**kwargs):
        return issue(self.request,self.root,self.policy,kwargs.pop('approvals',self.approvals()),kwargs.pop('authorities',self.authorities),self.journal,
            issuer_key_id='test-issuer',as_of=kwargs.pop('as_of',NOW),verifier=kwargs.pop('verifier',self.verifier),**kwargs)
    def verify(self,c,**kwargs):
        return verify(c,self.request,self.root,self.policy,kwargs.pop('approvals',self.approvals()),kwargs.pop('authorities',self.authorities),self.journal,
            as_of=kwargs.pop('as_of',NOW),verifier=kwargs.pop('verifier',self.verifier),**kwargs)

class Case(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.f=Fixture(Path(self.tmp.name));self.root=self.f.root
    def codes(self):return {b['code'] for b in self.f.assess().blockers}
    def blocked(self,code):
        result=self.f.assess();self.assertFalse(result.ready_for_signing);self.assertIn(code,{b['code'] for b in result.blockers});return result
    def raises(self,code,fn,*args,**kwargs):
        with self.assertRaises(ContractError) as cm:fn(*args,**kwargs)
        self.assertEqual(cm.exception.code,code)
