"""SYNTHETIC authority fixtures. Ephemeral keys never leave process memory."""
from pathlib import Path
from dataclasses import replace,asdict
import sys,json,hashlib,tempfile,unittest,os,copy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from bie.qa.assurance_quality_v2.common import *
from bie.qa.assurance_quality_v2.authority import *
from bie.qa.assurance_quality_v2.rights import *
from bie.qa.assurance_quality_v2.harness import *
from bie.qa.assurance_quality_v2.memory import *
from bie.qa.operational_quality_v2.runtime import Program
from bie.qa.operational_quality_v2.common import tool_identity
from bie.qa.operational_quality_v2.publication import PublicationStore
NOW=10000

class Keys:
    def __init__(self):
        self.private={};keys=[]
        for purpose in PURPOSES:
            for i in range(2 if purpose=='clock' else 1):
                name=purpose+str(i);key=Ed25519PrivateKey.generate();self.private[name]=key
                keys.append(PublicAuthority(name,'p-'+name,'g-'+name,key.public_key().public_bytes_raw().hex(),(purpose,),0,3_000_000_000))
        self.keys=tuple(keys)
    def policy(self,**kw):return TrustPolicy('trust','tenant',self.keys,**kw)
    def envelope(self,s,purpose,subject,payload,key_id=None,created=None,expires=None):
        key_id=key_id or purpose+'0';value=dict(schema_version='bie.qa.signed-assurance/1',key_id=key_id,purpose=purpose,
            subject_digest=subject,binding=asdict(s.binding),nonce=s.challenge['nonce'],created_at=NOW-10 if created is None else created,
            expires_at=NOW+120 if expires is None else expires,payload=payload,signature='0'*128)
        return self.resign(value)
    def resign(self,value):
        value=copy.deepcopy(value);value['signature']='0'*128
        value['signature']=self.private[value['key_id']].sign(signing_bytes(value)).hex();return value
    def establish(self,s,*,epoch=1,utc_ms=NOW*1000,revoked=()):
        clocks=tuple(self.envelope(s,'clock',s.challenge_digest,dict(utc_ms=utc_ms,uncertainty_ms=0,trust_digest=s.policy.content_digest),key_id='clock'+str(i)) for i in range(s.policy.clock_quorum))
        status=self.envelope(s,'status',s.policy.content_digest,dict(epoch=epoch,revoked_key_ids=list(revoked),trust_digest=s.policy.content_digest))
        return s.establish(clocks,status)
    def roles(self,s,subject,purposes=('capture','review','issuer')):
        return tuple(self.envelope(s,p,subject,dict(decision='APPROVE',trust_digest=s.policy.content_digest)) for p in purposes)

class Temp(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.k=Keys();self.clock=[0];self.binding=Binding('run','a'*40,'b'*64,'c'*64)
        self.journal=AuthorityJournal(self.root/'authority',create=True)
        self.session=AuthoritySession(self.k.policy(),self.binding,self.journal,monotonic_ns=lambda:self.clock[0])
    def tearDown(self):self.temp.cleanup()
    def error(self,code,fn,*args,**kw):
        with self.assertRaises(ContractError) as cm:fn(*args,**kw)
        self.assertIn(code,str(cm.exception))
    def ready(self):self.k.establish(self.session);return self.session
    def fresh(self,*,binding=None,policy=None):
        return AuthoritySession(policy or self.k.policy(),binding or self.binding,self.journal,monotonic_ns=lambda:self.clock[0])

def ref(root,name,path,data,role='report'):
    p=Path(root)/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    return ArtifactRef(name,path,identity(data),len(data),role)

def program(path,code,timeout=5):
    path=Path(path).absolute();path.write_text(code)
    exe=str(Path(sys.executable).resolve())
    return Program(path.stem,(exe,'-B',str(path)),tool_identity(exe)['sha256'],str(path),identity(path.read_bytes()),timeout)

STAGE_CODE='''import os,json,hashlib\nfrom pathlib import Path\ni=Path(os.environ['BIE_INPUT_ROOT']);o=Path(os.environ['BIE_OUTPUT_ROOT'])\nr=json.loads((i/'book-request.json').read_text())\ndef dg(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()\nv={'schema_version':'bie.qa.book-stage-result/1','stage':r['stage'],'run_id':os.environ['BIE_RUN_ID'],'execution_id':os.environ['BIE_EXECUTION_ID'],'request_digest':dg(r),'source_digest':r['source_digest'],'checks':[{'check_id':x,'status':'PASS'} for x in r['required_checks']]}\n(o/'qa-result.json').write_text(json.dumps(v))\n(o/'data.txt').write_text('DIAGNOSTIC')\n'''

def pipeline_fixture(root,*,all_stages=False,profile='DIAGNOSTIC',bad=''):
    root=Path(root);src=root/'source';src.mkdir();(src/'source.txt').write_text('Authored diagnostic source.')
    names=STAGES if all_stages else ('BI','KI');steps=[]
    for n in names:
        code=STAGE_CODE+'\n# independent '+n+'\n'
        if bad and n==names[-1]:code+=bad+'\n'
        p=program(root/(n.lower()+'.py'),code)
        st=Stage(n.lower(),'regression' if n in ('QA','EVAL') else 'compile',p,('qa-result.json','data.txt'))
        steps.append(PipelineStep(n,st,() if not steps else (steps[-1].name,),('basic-'+n,)))
    plan=BookPlan(tuple(inventory(src)),'source.txt',tuple(steps),profile=profile)
    binding=Binding('book-run','a'*40,digest(inventory(src)),plan.content_digest)
    return src,plan,binding

sys.path.insert(0,str(ROOT/'tests/qa_rights19'))
import rights19_support as rs

def rights_fixture(root,*,retrieval=False):
    root=Path(root);root.mkdir(exist_ok=True)
    req,rp=rs.make_fixture(root)
    if retrieval:
        rp=replace(rp,requirements=tuple(replace(u,operations=tuple(sorted(set(u.operations+('RETRIEVE',))))) for u in rp.requirements))
    rows=tuple(inventory(root));materials={m.artifact_id:m.material_id for m in rp.materials}
    provenance=tuple(dict(artifact_id=a.artifact_id,path=a.path,role='SOURCE' if a.role=='source' else 'EVIDENCE',
        material_id=materials.get(a.artifact_id,'evidence-'+a.artifact_id),parent_ids=[],provider_ids=[]) for a in req.snapshot.artifacts)
    policy=InventoryPolicy('inventory',rp.content_digest,rows,provenance,())
    binding=Binding('rights-run','a'*40,req.snapshot.content_digest,policy.content_digest)
    return req,rp,policy,binding

def memory_fixture(root,keys,clock):
    src=Path(root)/'content';src.mkdir()
    req,rp=rs.make_fixture(src)
    refs={a.artifact_id:a for a in req.snapshot.artifacts}
    before=ref(src,'before','before.txt',b'A square has three sides.','support')
    validation_body={'schema_version':'bie.qa.correction-validation/1','source_sha256':refs['source'].sha256,
        'before_sha256':before.sha256,'after_sha256':refs['lesson'].sha256,'revision':'a'*40,
        'conditions_preserved':True,'cases':[{'case_id':'sides','before':'FAIL','after':'PASS'},{'case_id':'caption','before':'PASS','after':'PASS'}]}
    validation=ref(src,'validation','validation.json',canonical_bytes(validation_body))
    status=ref(src,'rights-status',refs['rights-status'].path,rs.status_blob(grants=('source-grant','asset-grant','memory-grant')))
    arts=tuple(a for a in req.snapshot.artifacts if a.artifact_id!='rights-status')+(before,validation,status)
    snap=replace(req.snapshot,artifacts=arts)
    from bie.qa.rights_v2.models import Material,Grant,UseRequirement,UseSelection
    material=Material('correction','lesson','ASSET','whole','GENERATED','authored-fixture:correction','LicenseRef-Memory',('book',))
    grant=replace(rp.grants[0],grant_id='memory-grant',material_id='correction',license_atom='LicenseRef-Memory',operations=('RETRIEVE',),obligations=())
    rp=replace(rp,snapshot_digest=snap.content_digest,materials=rp.materials+(material,),
        grants=tuple(replace(g,operations=g.operations+('RETRIEVE',)) for g in rp.grants)+(grant,),
        requirements=tuple(replace(u,operations=u.operations+('RETRIEVE',)) for u in rp.requirements)+
            (UseRequirement('memory-use','correction','lesson',('RETRIEVE',),'LicenseRef-Output'),))
    req=replace(req,snapshot=snap,selections=req.selections+(UseSelection('memory-use',('memory-grant',)),))
    mats={m.artifact_id:m.material_id for m in rp.materials}
    ip=InventoryPolicy('memory-inventory',rp.content_digest,tuple(inventory(src)),
        tuple(dict(artifact_id=a.artifact_id,path=a.path,role='SOURCE' if a.role=='source' else 'EVIDENCE',material_id=mats.get(a.artifact_id,'ev-'+a.artifact_id),parent_ids=[],provider_ids=[]) for a in arts),())
    rb=Binding('rights-run','a'*40,snap.content_digest,ip.content_digest)
    rj=AuthorityJournal(Path(root)/'rights-authority',create=True);rses=AuthoritySession(keys.policy(),rb,rj,monotonic_ns=lambda:clock[0]);keys.establish(rses)
    clearance=keys.envelope(rses,'rights',clearance_subject(req,rp,ip,rb),dict(decision='APPROVE',trust_digest=rses.policy.content_digest))
    rc=RightsContext(req,src,rp,ip,rb,rs.reviews_for(req,rp),rs.ReviewVerifier((rs.KEY,)),rses,clearance)
    plan=CorrectionPlan('correction',refs['source'],before,refs['lesson'],validation,'math','en','grade4','a'*40,
        ('sides','caption'),('sides',),('source','semantic','regression'),clearance_subject(req,rp,ip,rb))
    b=Binding('memory-run','a'*40,refs['lesson'].sha256,plan.content_digest)
    return src,plan,b,rc
