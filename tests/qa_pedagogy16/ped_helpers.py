"""Authored synthetic curriculum, not a real learner or assessor service."""
from pathlib import Path
from dataclasses import replace,asdict
import hashlib,hmac,tempfile,unittest,json
from bie.qa.release_v2.contracts import ArtifactRef,ReleaseCandidate,ContractError,canonical_bytes
from bie.qa.source_v2.models import Source,Block,Output,Citation,Claim,Request,Policy
from bie.qa.source_v2.attestation import Assessment,AssessmentKey,AssessmentVerifier
from bie.qa.pedagogy_v2 import *
from bie.qa.pedagogy_v2.attestation import review_targets
NOW=1800000000
REV='375d99af0edd0086206817dae932156ddf61c569'

def artifact(root,path,payload,aid,role='support'):
 p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
 return ArtifactRef(aid,path,hashlib.sha256(payload).hexdigest(),len(payload),role)

def fixture(root):
 sentences=[]
 for n in (1,2):
  topic='equal groups' if n==1 else 'multiplication as repeated addition'
  sentences.extend([
   (f'c{n}-objective',f'Explain and apply {topic}.','INSTRUCTION'),
   (f'c{n}-explanation',f'Lesson {n}: show equal-sized groups, count each group, and count the total.','FACT'),
   (f'c{n}-example',f'Example {n}: {n+1} groups of 3 objects contain {3*(n+1)} objects altogether.','FACT'),
   (f'c{n}-rubric',f'For objective {n}, award up to 5 points for the model and 5 points for the justified total.','INSTRUCTION'),
   (f'c{n}-prompt',f'For a new arrangement with {n+3} groups of 2 objects, draw a model and justify the total.','QUESTION'),
   (f'c{n}-solution',f'Answer {n}: draw {n+3} pairs and count {2*(n+3)} objects.','FACT'),
   (f'c{n}-feedback',f'Feedback {n}: check that all groups have two objects and that the count includes every group.','INSTRUCTION')])
 text='\n'.join(s for cid,s,k in sentences)
 sr=artifact(root,'sources/authored-pedagogy.txt',text.encode(),'ped-source','source')
 out=artifact(root,'outputs/pedagogy-script.txt',text.encode(),'ped-script')
 v=artifact(root,'fixtures/video.bin',b'NOT_A_RENDER_SYNTHETIC','fixture-video','video')
 g=artifact(root,'fixtures/game.bin',b'NOT_A_GAME_SYNTHETIC','fixture-game','game')
 candidate=ReleaseCandidate('2.0.0','ped-candidate','ped-run',REV,(sr,out,v,g))
 source=Source('authored-ped',sr,'utf8',1)
 block=Block('ped-block','authored-ped',sr.sha256,1,'ped-region',(0,0,1000000,1000000),text,'utf8','1',1000000)
 claims=[];citations=[];pos=0
 for cid,s,kind in sentences:
  cite='cite-'+cid;citations.append(Citation(cite,block.block_id,block.content_digest,pos,pos+len(s),s))
  claims.append(Claim(cid,'ped-output',out.sha256,pos,pos+len(s),s,kind,(cite,)));pos+=len(s)+1
 src=Request('1.0.0','ped-run',REV,candidate.content_digest,(source,),(block,),(Output('ped-output',out,'lesson'),),tuple(citations),tuple(claims))
 requirements=[];objectives=[];segments=[];events=[];teaching=[];items=[]
 for n in (1,2):
  oid=f'obj-{n}';concept=f'concept-{n}';ids=(f'criterion-{n}-model',f'criterion-{n}-total')
  criteria=(Criterion(ids[0],'Represent the groups',5,3),Criterion(ids[1],'Justify the total',5,3))
  req=ObjectiveRequirement(oid,concept,'Construct a group model and justify the total',('APPLY',),criteria,() if n==1 else ('obj-1',),transfer_required=True)
  requirements.append(req);objectives.append(Objective(oid,concept,'APPLY',(f'c{n}-objective',),ids,(f'cite-c{n}-objective',),800000))
  ins=f'instruction-{n}';ass=f'assessment-{n}';segments.extend((Segment(ins,'instruction',30000),Segment(ass,'assessment',20000)))
  events.extend((
   Event(f'e{n}-objective',ins,0,3000,'screen',(f'c{n}-objective',),(),1),
   Event(f'e{n}-explanation',ins,3000,12000,'narration',(f'c{n}-explanation',),(concept,)),
   Event(f'e{n}-example',ins,12000,23000,'narration',(f'c{n}-example',),()),
   Event(f'e{n}-rubric',ins,23000,30000,'screen',(f'c{n}-rubric',),(),1),
   Event(f'e{n}-prompt',ass,0,3000,'prompt',(f'c{n}-prompt',),(),1),
   Event(f'e{n}-solution',ass,6000,12000,'solution',(f'c{n}-solution',),(),1,0,True),
   Event(f'e{n}-feedback',ass,12000,20000,'feedback',(f'c{n}-feedback',),(),1,0,True)))
  teaching.extend((Teaching(f'teach-{n}',oid,ids,(f'e{n}-explanation',),'APPLY','explanation'),Teaching(f'example-{n}',oid,ids,(f'e{n}-example',),'APPLY','worked_example')))
  items.append(AssessmentItem(f'item-{n}',oid,'mastery','APPLY','constructed',True,ids,f'e{n}-prompt',f'e{n}-solution',f'e{n}-feedback',(f'c{n}-rubric',),tuple((c,5) for c in ids)))
 sids=tuple(s.segment_id for s in segments);routes=(Route('core-route',sids),)
 policy=PedagogyPolicy('ped-test-policy',Policy('ped-source-policy',('ped-output',)),'beginner','en',tuple(requirements),sids,(RouteRequirement('core-route',sids,('obj-1','obj-2'),200000),),(OrderConstraint('foundation-first','instruction-1','instruction-2'),),LoadLimits(4,3,2,4000,3,180000,5000))
 return PedagogyRequest('1.0.0',src,'beginner','en',tuple(objectives),tuple(segments),tuple(events),tuple(teaching),tuple(items),routes),policy,candidate

def key(**changes):return replace(ReviewKey('ped-key',b'SYNTHETIC_PED_TEST_KEY_NOT_PRODUCTION_001','ped-assessor','1','ped-review-group',('inventory','mapping','teaching','support'),'operator_managed'),**changes)
def source_key(**changes):return replace(AssessmentKey('source-key',b'SYNTHETIC_PED_SOURCE_KEY_NOT_PRODUCTION_01','source-assessor','1',('semantic','extraction','nonfactual'),'operator_managed'),**changes)
def sign(a,k):return replace(a,signature=hmac.new(k.secret,a.signing_bytes(),hashlib.sha256).hexdigest())
def signed_reviews(request,policy,k=None):
 k=k or key();rd=request.content_digest;pd=policy.content_digest
 return tuple(sign(Review(f'ped-review-{i}-{k.key_id}',rd,pd,s,p,'VERIFIED',e,950000,'SYNTHETIC assessment fixture; not actual contextual review.',k.evaluator_id,k.evaluator_version,NOW-10,NOW+60,k.key_id),k) for i,((p,s),e) in enumerate(sorted(review_targets(request).items())))
def source_reviews(request,policy,k=None):
 k=k or source_key();rd=request.source.content_digest;pd=policy.source.content_digest
 return tuple(sign(Assessment(f'source-{c.claim_id}',rd,pd,c.claim_id,'semantic' if c.kind=='FACT' else 'nonfactual','SUPPORTED' if c.kind=='FACT' else 'NO_FACTUAL_ASSERTION',950000,'SYNTHETIC source assessment fixture.',k.evaluator_id,k.evaluator_version,NOW-10,NOW+60,k.key_id),k) for c in request.source.claims)
def options(r,p,**changes):
 k=key();sk=source_key();o=dict(reviews=signed_reviews(r,p,k),verifier=ReviewVerifier((k,)),source_assessments=source_reviews(r,p,sk),source_verifier=AssessmentVerifier((sk,)));o.update(changes);return o

def change(rows,key,value,**kwargs):return tuple(replace(x,**kwargs) if getattr(x,key)==value else x for x in rows)
def codes(report):return {f.code for f in report.findings}
class FixtureCase(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.request,self.policy,self.candidate=fixture(self.root)
 def run_check(self,r=None,p=None,**kw):
  r=self.request if r is None else r;p=self.policy if p is None else p
  return evaluate(r,self.root,p,as_of=NOW,**options(r,p,**kw))
 def assertCode(self,result,area,code,status=None):
  report=getattr(result,area);self.assertIn(code,codes(report))
  if status:self.assertEqual(report.status,status)
  self.assertFalse(result.product_accepted)
 def event(self,eid,**kw):return replace(self.request,events=change(self.request.events,'event_id',eid,**kw))
 def spec(self,oid='obj-1',**kw):return replace(self.policy,objectives=change(self.policy.objectives,'objective_id',oid,**kw))
 def limit(self,**kw):return replace(self.policy,load_limits=replace(self.policy.load_limits,**kw))
