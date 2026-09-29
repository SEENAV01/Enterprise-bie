"""Authored diagnostics only. Every signing credential here is SYNTHETIC."""
from pathlib import Path
from dataclasses import asdict,replace
import hashlib,json,hmac,tempfile,unittest,sys
from bie.qa.native_quality_v2.common import *
from bie.qa.native_quality_v2.documents import *
from bie.qa.native_quality_v2.knowledge import *
from bie.qa.native_quality_v2.assessors import *
from bie.qa.native_quality_v2.calibration import *
from bie.qa.native_quality_v2.readiness import *
from bie.qa.reasoning_v2.attestation import ReviewKey
from bie.qa.source_v2.models import Output,Policy as SourcePolicy
from bie.prerequisite_intelligence.graph import build_graph,Edge
NOW=1800000000
REV='a'*40
CAND=digest('synthetic-candidate')
SENTENCE='Force is proportional to mass when acceleration is constant.'
SYNTHETIC_KEY=ReviewKey('synthetic-key',b'SYNTHETIC-NOT-A-PRODUCTION-KEY-0001','test-reviewer','v1','synthetic-group',('calibration','mastery','mapping'),'operator_managed')

def save(root,path,value,role='support',identifier=None):
    data=value if type(value) is bytes else canonical_bytes(value)
    p=Path(root)/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    return ArtifactRef(identifier or path.replace('/','-').replace('.','-'),path,hashlib.sha256(data).hexdigest(),len(data),role)

def bound(policy):return Binding('diagnostic-run',REV,CAND,policy.content_digest)
def codes(report):return {f.code for f in report.findings}
def signed(subject,purpose,request_digest,policy_digest,evidence_ids,*,key=SYNTHETIC_KEY,verdict='VERIFIED',issued=NOW-1,expires=NOW+100):
    r=Review('synthetic-review-'+subject,request_digest,policy_digest,subject,purpose,verdict,tuple(evidence_ids),1000000,'SYNTHETIC TEST ASSESSMENT ONLY',key.evaluator_id,key.evaluator_version,issued,expires,key.key_id)
    return replace(r,signature=hmac.new(key.secret,r.signing_bytes(),hashlib.sha256).hexdigest())

def text_pdf(lines=(SENTENCE,),draw=False):
    import pymupdf
    d=pymupdf.open();p=d.new_page(width=600,height=300)
    for i,line in enumerate(lines):p.insert_text((30,40+25*i),line,fontsize=12)
    if draw:p.draw_rect(pymupdf.Rect(25,150,100,200),fill=(0,0,0))
    data=d.tobytes(no_new_id=True);d.close();return data
PDF_BYTES=text_pdf()

def doc_fixture(root):
    pol=DocumentPolicy();b=bound(pol);ref=save(root,'source.pdf',PDF_BYTES,'source','source-pdf')
    snap=inspect_pdf(ref,root,b,pol);r=verify_document(snap,ref,root,b,pol)
    source,blocks=to_source_records(snap,ref,verified_report=r)
    return pol,b,ref,snap,source,blocks

def knowledge_fixture(root,sentence=SENTENCE):
    dp,b,ref,snap,source,blocks=doc_fixture(root)
    if sentence!=SENTENCE:
        ref=save(root,'source.pdf',text_pdf((sentence,)),'source','source-pdf');snap=inspect_pdf(ref,root,b,dp)
        source,blocks=to_source_records(snap,ref,verified_report=verify_document(snap,ref,root,b,dp))
    native=native_claims(blocks[0],(sentence,));ids=tuple(r['claim_id'] for r in native)
    conditions=('when acceleration is constant',) if sentence==SENTENCE else ()
    kp=KnowledgePolicy(ids,(ConceptFacet('facet-1','force',(blocks[0].block_id,),conditions),),('independent-reference',))
    kb=bound(kp);outref=save(root,'output.txt',sentence.encode(),identifier='output-text');out=Output('output-1',outref,'narration')
    req=source_request(source,blocks,out,sentence,native,{ids[0]:(0,len(sentence))},kb)
    sp=SourcePolicy('source-policy',('output-1',));ind=save(root,'reference.txt',b'Independent reviewed reference fixture.','support','independent-reference')
    return req,sp,kp,kb,{'facet-1':ids},(ind,)

def calibration_fixture(root):
    cp=CalibrationPolicy((CriterionFloor('academic',800000,True),CriterionFloor('teaching',700000,False)),
      (RaterIdentity('rater1','v1','principal1','group1'),RaterIdentity('rater2','v1','principal2','group2')),'physics','en')
    b=bound(cp)
    corpus=dict(schema_version='bie.qa.calibration-corpus/1',corpus_id='corpus1',domain='physics',language='en',rubric_digest=cp.content_digest,created_at=NOW-5,
      training_source_hashes=[],cases=[dict(case_id='case'+str(i),source_sha256=digest('source'+str(i)),input_sha256=digest('input'+str(i)),split='holdout',labels={'academic':i<2,'teaching':i<2},blind_id='blind'+str(i)) for i in range(4)],provenance_mode='diagnostic')
    cr=save(root,'corpus.json',corpus,identifier='corpus')
    pred=dict(schema_version='bie.qa.calibration-predictions/1',corpus_sha256=cr.sha256,policy_digest=cp.content_digest,raters=[asdict(r) for r in cp.raters],
        predictions=[dict(case_id=c['case_id'],rater_id=r.rater_id,scores={k:900000 if v else 100000 for k,v in c['labels'].items()}) for c in corpus['cases'] for r in cp.raters])
    pr=save(root,'predictions.json',pred,identifier='predictions')
    return cp,b,corpus,pred,cr,pr

def readiness_fixture(root):
    rp=ReadinessPolicy(('a','b','c'),('default','alternate'),('math_correctness','reasoning_validity'),(('knowledge',800000),('application',800000)),850000)
    b=bound(rp);graph=build_graph(('a','b','c'),(Edge('a','b'),Edge('b','c')))
    lesson=dict(schema_version='bie.qa.native-lesson-scope/1',learner_id='learner1',binding=asdict(b),routes=[dict(route_id=r,concept_order=['a','b','c']) for r in rp.required_routes],
       source_claim_ids=['claim1'],applicability=[])
    lr=save(root,'lesson.json',lesson,identifier='lesson')
    return rp,b,graph,lesson,lr

class TempCase(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def blocked(self,r,code):self.assertEqual(r.status,'BLOCKED');self.assertIn(code,codes(r))
