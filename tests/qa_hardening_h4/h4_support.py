"""Authored diagnostic artifacts only; no production credentials or learner data."""
import unittest,tempfile,hashlib,copy
from pathlib import Path
from dataclasses import asdict,replace
from io import BytesIO
from PIL import Image
from bie.qa.domain_quality_v2.common import *
from bie.qa.domain_quality_v2.reasoning import *
from bie.qa.domain_quality_v2.pedagogy import *
from bie.qa.domain_quality_v2.mathematics import *
from bie.qa.domain_quality_v2.director import *
from bie.qa.domain_quality_v2.visual import *
from bie.reasoning.decision_contracts import EvidenceRef
from bie.director.lesson_architecture_contract import LessonSceneIntent,build_lesson_architecture
from bie.director.script_plan import ScriptSegment,build_script_plan
from bie.visual_intelligence.layout_contracts import Box,LayoutNode,make_layout_plan
NOW=1800000000
SOURCE='Acceleration causes velocity change when the net force is nonzero. बल का प्रभाव समझें।'
REV='a'*40

def save(root,path,data,role='support',aid=None):
    data=data if type(data)is bytes else canonical_bytes(data)
    p=Path(root)/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    return ArtifactRef(aid or path.replace('.','-'),path,hashlib.sha256(data).hexdigest(),len(data),role)

def binding(p):return Binding('h4-diagnostic-run',REV,digest('synthetic-candidate'),p.content_digest)
def payload(task,b,**kw):return dict(schema_version=SCHEMA,task_id=task,binding=asdict(b),**kw)
def codes(r):return {f.code for f in r.findings}

def reason_fixture(root):
    s=save(root,'source.txt',SOURCE.encode(),'source','src')
    native=tuple(ReasoningDecision(d,'causal_explanation','subject','Why?','explain','when the net force is nonzero',0.9,[EvidenceRef('src','primary',0.9)])for d in ('cause','time','space'))
    pol=ReasonPolicy(('cause','time','space'),(('cause','src','when the net force is nonzero'),),(('force','motion','mechanism'),),
        (('first','0','1'),('second','2','3')),(('world','1','0','0','1','0','0'),('shifted','1','0','0','1','10','0')))
    b=binding(pol);d=payload('BIE-QA-HARD-012',b,native_digest=native_digest([asdict(x)for x in native]),claims=[
      dict(decision_id='cause',kind='causal',cause='force',effect='motion',assertion='causes'),
      dict(decision_id='time',kind='temporal',before='first',after='second',clock='common_rational_time'),
      dict(decision_id='space',kind='spatial',left=dict(frame='world',x='0',y='0'),right=dict(frame='shifted',x='0',y='0'),relation='left_of')])
    return pol,b,native,(s,),d

def pedagogy_fixture(root):
    s=save(root,'source.txt',SOURCE.encode(),'source','src')
    arch=build_lesson_architecture('lesson','Lesson',(LessonSceneIntent('teach','explain',('obj',),('src',)),LessonSceneIntent('test','apply',('obj',),('src',),('teach',))),('obj',),('src',),'v1')
    cells=(AssessmentCell('obj','concept','APPLY',None,True,('item',),('src',)),)
    p=RoutePolicy((('default',('teach','test')),('alternate',('teach','test'))),(('obj','concept','APPLY',True),),(('item','The answer is four'),),(('item','teach'),))
    b=binding(p);events=[dict(event_id='p',kind='prompt',item_id='item',scene_id='test',at_ms=0,text='Predict the result',correct=None),
        dict(event_id='r',kind='response',item_id='item',scene_id='test',at_ms=1500,text='The answer is four',correct=True),
        dict(event_id='f',kind='feedback',item_id='item',scene_id='test',at_ms=1600,text='The answer is four',correct=None)]
    d=payload('BIE-QA-HARD-013',b,native_digest=digest(dict(architecture=asdict(arch),cells=[asdict(c)for c in cells])),mode='diagnostic',captured_at=NOW-2,
      routes=[dict(route_id=r,scene_order=list(seq),events=copy.deepcopy(events))for r,seq in p.routes])
    return p,b,arch,cells,(s,),d

def director_fixture(root):
    s=save(root,'source.txt',SOURCE.encode(),'source','src')
    native=build_script_plan('lesson',(ScriptSegment('hook','scene1','hook','Why does velocity change?',('src',),('obj',)),
        ScriptSegment('payoff','scene2','explanation','Acceleration changes velocity when the net force is nonzero. बल का प्रभाव समझें।',('src',),('obj',))),'neutral')
    p=DirectorPolicy(('hook','payoff'),('obj',),(('payoff','src','when the net force is nonzero'),),(('hook','payoff'),),(('payoff','hi','बल'),),
        (('academic',900000),('explanation',800000),('source_fidelity',900000),('cinematic',700000)))
    b=binding(p);d=payload('BIE-QA-HARD-016',b,native_digest=digest(asdict(native)),timeline=[dict(segment_id='hook',language='en',start_ms=0,end_ms=2000,role='hook'),
        dict(segment_id='payoff',language='hi',start_ms=2000,end_ms=10000,role='explanation')],ratings={c:1000000 for c,f in p.rubric_floors},rated_at=NOW-1,provenance_mode='diagnostic')
    return p,b,native,(s,),d

HTML="""<!doctype html><html><head><style>body{margin:0} [data-h4-id]{position:absolute;box-sizing:border-box;font:18px sans-serif;padding:0;margin:0;height:40px;width:120px;top:20px}#a{left:20px}#b{left:200px}</style></head><body><div id="a" data-h4-id="a">Cause</div><div id="b" data-h4-id="b">Effect</div></body></html>"""

def visual_fixture(root):
    s=save(root,'source.txt',b'Cause precedes Effect.','source','src');h=save(root,'scene.html',HTML.encode(),aid='html')
    nodes=(LayoutNode('a','label',Box(.05,.1,.3,.2),('src',),payload={'text':'Cause'}),LayoutNode('b','label',Box(.5,.1,.3,.2),('src',),payload={'text':'Effect'}))
    native=make_layout_plan(evidence_refs=('src',),reasoning_refs=('reason',),nodes=nodes)
    p=VisualPolicy((400,200),('a','b'),(('a','left_of','b'),));b=binding(p)
    img=Image.new('RGB',p.viewport);buf=BytesIO();img.save(buf,format='PNG');png=buf.getvalue()
    obs=dict(schema_version='bie.qa.h4-static-capture/1',html_sha256=h.sha256,viewport=list(p.viewport),nodes=[dict(id=n.node_id,text=n.payload['text'],rect=[n.box.x*400,n.box.y*200,n.box.width*400,n.box.height*200],visible=True,clipped=False,hit_samples=[True]*5,unsupported=False)for n in nodes],
      unsupported_markup=0,blocked_requests=[],browser_version='SYNTHETIC_FIXTURE',png_sha256=hashlib.sha256(png).hexdigest(),execution_mode='controlled_static_about_blank',native_runtime_verified=False,browser_sandbox_verified=False)
    return p,b,native,h,(s,),obs,png

class TempCase(unittest.TestCase):
    def setUp(self):self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
    def tearDown(self):self.t.cleanup()
    def blocked(self,r,code):self.assertEqual(r.status,'BLOCKED');self.assertIn(code,codes(r))
