"""All positive authorizations and permissions are SYNTHETIC diagnostic fixtures."""
import sys,os,json,tempfile,unittest,hashlib,hmac
from pathlib import Path
from dataclasses import replace,asdict
from bie.qa.operational_quality_v2.common import *
from bie.qa.operational_quality_v2.runtime import *
from bie.qa.operational_quality_v2.dependencies import *
from bie.qa.operational_quality_v2.reproduction import *
from bie.qa.operational_quality_v2.rebuild import *
from bie.qa.operational_quality_v2.performance import *
from bie.qa.operational_quality_v2.publication import *
from bie.qa.reasoning_v2.attestation import Review,ReviewVerifier,ReviewKey
from bie.qa.lifecycle_quality_v2.common import make_change
NOW=1790550000
KEY=ReviewKey('H7-test',b'H7-SYNTHETIC-TEST-CREDENTIAL-ONLY-000000','H7-assessor','1','independent-test',('inference',),'operator_managed')
VERIFIER=ReviewVerifier((KEY,))

def signed(change,scope):
    r=Review('h7-review',change.content_digest,scope.content_digest,change.target.artifact_id,'inference','VERIFIED',
        tuple(x.artifact_id for x in change.input_refs),1000000,'SYNTHETIC approvals only',KEY.evaluator_id,'1',NOW-1,NOW+1000,KEY.key_id)
    return replace(r,signature=hmac.new(KEY.secret,r.signing_bytes(),hashlib.sha256).hexdigest())

def make_program(path,text_,name='worker',timeout=10,max_log=1024*1024):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text_)
    exe=Path(sys.executable).resolve()
    return Program(name,(str(exe),'-I','-B',str(path)),identity(exe.read_bytes()),str(path),identity(path.read_bytes()),timeout,max_log)

def dependency_fixture(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    (root/'package').mkdir(exist_ok=True)
    (root/'package/METADATA').write_text('Name: bie-diagnostic-dependency\nVersion: 1.0\n')
    (root/'package/value.txt').write_text('42')
    rows=tuple(inventory(root));packages=(dict(package_id='dep',ecosystem='PyPI',name='bie-diagnostic-dependency',version='1.0',
        metadata_path='package/METADATA',paths=[x['path'] for x in rows],dependencies=[]),)
    p=DependencyPolicy(rows,packages)
    r=dict(schema_version='bie.qa.dependency-review/1',policy_digest=p.content_digest,created_at=NOW-5,expires_at=NOW+1000,
        snapshot_kind='SYNTHETIC',packages=[dict(package_id='dep',version='1.0',status='NO_KNOWN_FINDINGS',advisory_ids=[])])
    return p,r


def build_fixture(base,*,bad_caption=False,require_native=False):
    root=Path(base)/'original';root.mkdir();(root/'generated').mkdir();(root/'source').mkdir()
    (root/'generated/data.json').write_text(json.dumps({'value':4,'caption':'keep source condition'}))
    (root/'source/book.txt').write_text('two plus three equals five; keep source condition')
    refs=[ArtifactRef('target','generated/data.json',identity((root/'generated/data.json').read_bytes()),(root/'generated/data.json').stat().st_size,'report'),
          ArtifactRef('book','source/book.txt',identity((root/'source/book.txt').read_bytes()),(root/'source/book.txt').stat().st_size,'source')]
    scope=RepairScope('MATH',('generated/data.json',),('source/book.txt',),('compile','render','capture','regression'),('video','captions','regression'),'generator-test')
    binding=Binding('h7-fixture','a'*40,digest(inventory(root)),scope.content_digest)
    payload=canonical_bytes({'value':5,'caption':'BROKEN' if bad_caption else 'keep source condition'})
    change=make_change('BIE-QA-HARD-027',binding,root,refs[0],payload,scope,(refs[1],),{'synthetic':True})
    stages=[]
    for role in ('compile','render','capture','regression'):
        code="import os,json,hashlib\nfrom pathlib import Path\ni=Path(os.environ['BIE_INPUT_ROOT']);o=Path(os.environ['BIE_OUTPUT_ROOT'])\n"
        code+="d=json.loads((i/'generated/data.json').read_text())\n"
        if role=='regression':
            code+="r={'execution_id':os.environ['BIE_EXECUTION_ID'],'run_id':os.environ['BIE_RUN_ID'],'cases':[{'case_id':'math','status':'PASS' if d['value']==5 else 'FAIL'},{'case_id':'caption','status':'PASS' if d['caption']=='keep source condition' else 'FAIL'}]};(o/'result.json').write_text(json.dumps(r))\n"
            paths=('result.json',)
        else:
            code+="(o/'"+role+".json').write_text(json.dumps(d,sort_keys=True))\n";paths=(role+'.json',)
        program=make_program(Path(base)/'tools'/(role+'.py'),code,name=role)
        stages.append(Stage(role,role,program,paths))
    p=RebuildPolicy(tuple(inventory(root)),tuple(stages),('math','caption'),('math',),require_native)
    return root,change,scope,p

class Temp(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def error(self,code,fn,*args,**kwargs):
        with self.assertRaises(ContractError) as cm:fn(*args,**kwargs)
        self.assertEqual(cm.exception.code,code)
    def binding(self,p):return Binding('run','a'*40,'b'*64,p.content_digest)
