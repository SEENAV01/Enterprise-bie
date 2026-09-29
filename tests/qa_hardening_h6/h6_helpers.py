"""All positive identities, approvals, datasets and clocks here are SYNTHETIC."""
from pathlib import Path
from dataclasses import asdict,replace
import hashlib,hmac,json,tempfile,unittest,sys,os,subprocess,time
from bie.qa.lifecycle_quality_v2.common import *
from bie.qa.lifecycle_quality_v2.accessibility import *
from bie.qa.lifecycle_quality_v2.repairs import *
from bie.qa.lifecycle_quality_v2.durable import *
from bie.qa.lifecycle_quality_v2.corpus import *
from bie.qa.lifecycle_quality_v2.workers import *
from bie.qa.reasoning_v2.attestation import ReviewKey
NOW=1800000000
KEY=ReviewKey('h6-test',b'SYNTHETIC_H6_REVIEW_SECRET_NOT_FOR_PRODUCTION','independent-test-reviewer','v1','independent-test-group',('inference','inventory'),'operator_managed')

def save(root,path,value,role='support',aid=None):
    value=value if type(value) is bytes else canonical_bytes(value)
    p=Path(root)/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value)
    return ArtifactRef(aid or path.replace('/','-').replace('.','-'),path,hashlib.sha256(value).hexdigest(),len(value),role)

def bound(policy,candidate=None):return Binding('h6-diagnostic','a'*40,candidate or digest('candidate'),policy.content_digest)
def signed(change,scope,key=KEY,verdict='VERIFIED',now=NOW):
    r=Review('h6-review',change.content_digest,scope.content_digest,change.target.artifact_id,'inference',verdict,
       tuple(a.artifact_id for a in change.input_refs),1000000,'SYNTHETIC TEST ASSESSMENT ONLY',key.evaluator_id,key.evaluator_version,now-1,now+100,key.key_id)
    return replace(r,signature=hmac.new(key.secret,r.signing_bytes(),hashlib.sha256).hexdigest())
def scope(target='generated/content.json',owner='DIR'):
    return RepairScope(owner,(target,),('source/book.txt',),('source','semantic','regression'),('source','semantic','regression','render'),'generator-test-group')

def good_generator(payload):
    d=strict_json(payload)['content']
    for r in d['records']:r['text']=r['text'].replace('is six','is five')
    return canonical_bytes(d)
def drops_condition(payload):
    d=strict_json(payload)['content'];d['records'][0]['text']='The result is five.';return canonical_bytes(d)
def invents_objective(payload):
    d=strict_json(payload)['content'];d['records'][0]['objective_ids']=['replacement'];return canonical_bytes(d)
def adds_record(payload):
    d=strict_json(payload)['content'];d['records'].append({**d['records'][0],'record_id':'new'});return canonical_bytes(d)
def authority_output(payload):return canonical_bytes({'release_authorized':True})
def no_change_generator(payload):return canonical_bytes(strict_json(payload)['content'])
def raises_generator(payload):raise ValueError('intentional diagnostic')
def slow_generator(payload):time.sleep(5);return b'{}'
def huge_generator(payload):return b'x'*100000

def cb(fn):return Callback(fn.__name__.replace('_','-'),validator_digest(fn),fn)

def content_fixture(root):
    src=save(root,'source/book.txt',b'Two plus three is five when counting exact integers.','source','source-book')
    doc=dict(schema_version='bie.qa.repair-content/1',domain='reasoning',sources=[asdict(src)],records=[dict(record_id='claim-1',text='Two plus three is six when counting exact integers.',source_ids=[src.artifact_id],objective_ids=['addition'],conditions=['when counting exact integers'])])
    target=save(root,'generated/content.json',doc,aid='content');p=scope(target.path,'RE');return target,p,bound(p),doc,src

def code_fixture(root,kind='ts'):
    raw=b'// generated diagnostic\nexport const total = 6;\nexport const unit = "items";\n'
    target=save(root,'generated/data.'+kind,raw,aid='module');p=replace(scope(target.path,'COMP'),required_checks=('compile','native-runtime','regression'),invalidates=('compile','native-runtime','regression','render'));b=bound(p)
    emitter=save(root,'support/emitter.txt',b'Pinned diagnostic emitter specification.','support','emitter')
    ir=save(root,'source/scene.json',{'answer':5},'source','scene');recipe=save(root,'support/recipe.json',{'schema_version':'diagnostic-recipe/1'},aid='recipe')
    start=raw.index(b'6');slot=LiteralSlot('total',start,start+1,hashlib.sha256(b'6').hexdigest(),'5')
    ownership=dict(schema_version='bie.qa.owned-module/1',binding=asdict(b),owner='COMP',module=asdict(target),emitter=asdict(emitter),source_ir=asdict(ir),recipe=asdict(recipe),slots=[{k:v for k,v in asdict(slot).items() if k!='value_json'}])
    o=save(root,'support/ownership.json',ownership,aid='ownership');return target,p,b,o,(slot,),ownership

def source_fixture(root):
    import pymupdf
    doc=pymupdf.open();page=doc.new_page(width=500,height=280)
    page.insert_text((20,40),'Force equals mass times acceleration.')
    page.insert_text((20,85),'The relation uses constant mass in this example.')
    raw=doc.tobytes(no_new_id=True);doc.close()
    sr=save(root,'source/book.pdf',raw,'source','source-pdf');p=scope('generated/extraction.json','BI');b=bound(p);dp=DocumentPolicy()
    db=Binding(b.run_id,b.revision,b.candidate_digest,dp.content_digest);good=inspect_pdf(sr,root,db,dp)
    bad=json.loads(json.dumps(good));bad['regions'][0]['text']='Damaged extraction.'
    bad['content_digest']=digest({k:v for k,v in bad.items() if k!='content_digest'})
    tr=save(root,'generated/extraction.json',bad,aid='extraction');return sr,tr,p,b,dp,good,bad

def access_fixture(root):
    p=AccessibilityPolicy(('submit','reset'),('desktop',),('mass',),('caption-1',));b=bound(p)
    a=save(root,'captured.bin',b'EXPLICIT SYNTHETIC CAPTURE RECORD','support','captured')
    v=dict(viewport_id='desktop',measured_axes=list(AXES),controls=[dict(control_id=c,name=c,keyboard_reached=True,focus_indicator=True,visible=True,contrast='7') for c in p.controls],
        meanings=[dict(meaning_id='mass',non_color_label='Mass in kilograms')],
        captions=[dict(caption_id='caption-1',text='Mass is measured.',visible=True,start_ms=0,end_ms=3000,contrast='7')],
        motion=dict(observed=True,mode='reduced',meaning_ids=['mass']),flash=dict(full_output_observed=True,screening='CLEAR',frame_count=100))
    d=dict(schema_version='bie.qa.output-accessibility/1',binding=asdict(b),created_at=NOW-1,execution_id='synthetic-capture',mode='SYNTHETIC_OBSERVATION',artifacts=[asdict(a)],views=[v])
    return p,b,d

def make_repo(root,defective=False):
    p=Path(root);p.mkdir();(p/'tests').mkdir()
    (p/'tests/test_case.py').write_text('import unittest\nclass Case(unittest.TestCase):\n def test_addition(self):self.assertEqual(2+3,'+('6' if defective else '5')+')\n def test_units(self):self.assertEqual(1000//1000,1)\n')
    env={**os.environ,'GIT_AUTHOR_NAME':'Synthetic BIE Test','GIT_AUTHOR_EMAIL':'test@example.invalid','GIT_COMMITTER_NAME':'Synthetic BIE Test','GIT_COMMITTER_EMAIL':'test@example.invalid','GIT_AUTHOR_DATE':'2026-01-01T00:00:00Z','GIT_COMMITTER_DATE':'2026-01-01T00:00:00Z'}
    for cmd in (['git','init','-q',str(p)],['git','-C',str(p),'add','.'],['git','-C',str(p),'commit','-qm','Authored diagnostic only']):subprocess.run(cmd,check=True,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    rev=subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD']).decode().strip();tree=subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD^{tree}']).decode().strip()
    return CorpusPolicy('authored-diagnostic-not-Enterprise-bie',rev,tree,(Suite('unit','tests'),))

class Temp(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def error(self,code,fn,*args,**kwargs):
        with self.assertRaises(ContractError) as e:fn(*args,**kwargs)
        self.assertEqual(e.exception.code,code)
    def blocked(self,r,code):
        self.assertEqual(r['report']['status'],'BLOCKED');self.assertIn(code,{f['code'] for f in r['report']['findings']})
