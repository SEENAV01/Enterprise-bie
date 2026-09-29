"""Authored fixtures only. SYNTHETIC grants, evaluator keys and assessment clock.

No supplied permission here authorizes use of a real textbook, asset or voice.
Positive tests use operator_managed to exercise the protocol, not real clearance.
"""
from pathlib import Path
from dataclasses import replace,asdict
import hashlib,hmac,json
from bie.qa.release_v2.contracts import ArtifactRef,canonical_bytes
from bie.qa.repair_v2.models import Snapshot
from bie.qa.rights_v2 import *
from bie.qa.reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier

NOW=10000
KEY=ReviewKey('synthetic-rights-key',b'SYNTHETIC-FIXTURE-SECRET-NOT-AUTHORITY-19','fixture-rights-reviewer','1','fixture-group',('inventory','support','mapping','disclosure','inference'),'operator_managed')

def status_blob(grants=('source-grant','asset-grant'),state='ACTIVE',observed_at=NOW):
    return canonical_bytes(dict(schema_version='bie.qa.rights-status/1',observed_at=observed_at,grants=[dict(grant_id=g,state=state) for g in grants]))

def make_fixture(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    blobs={'source':('source/book.txt',b'Authored diagnostic: a square has four equal sides.','source'),
        'asset':('assets/diagram.txt',b'DIAGNOSTIC SQUARE DESCRIPTION NOT A RENDERED ASSET','support'),
        'lesson':('generated/lesson.txt',b'A square has four equal sides. This diagnostic is not released.','support'),
        'credits':('generated/credits.txt','Source: Diagnostic Author.\nAsset: Diagnostic Artist — modified.\nLicense: synthetic terms only.\n'.encode(),'support'),
        'terms-source':('rights/source-terms.txt',b'SYNTHETIC source grant. Reviewed fixture permissions, not real legal terms.','support'),
        'terms-asset':('rights/asset-terms.txt',b'SYNTHETIC asset grant. Reviewed fixture permissions, not real legal terms.','support'),
        'rights-status':('rights/status.json',status_blob(),'report')}
    arts=[]
    for aid,(p,b,role) in blobs.items():
        q=root/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b);arts.append(ArtifactRef(aid,p,hashlib.sha256(b).hexdigest(),len(b),role))
    snap=Snapshot('rights-run','a'*40,tuple(sorted(arts,key=lambda a:a.artifact_id)))
    source=Material('book','source','SOURCE','whole','THIRD_PARTY','authored-fixture:book','LicenseRef-Source')
    asset=Material('diagram','asset','ASSET','whole','GENERATED','authored-fixture:diagram','LicenseRef-Asset',('book',))
    common=dict(operations=('READ','EXTRACT','ADAPT','DISPLAY','DISTRIBUTE'),dimensions=('COPYRIGHT',),grantees=('bie-fixture',),territories=('WORLDWIDE',),channels=('ALL',),commercial_allowed=True,valid_from=0,valid_until=20000)
    g1=Grant('source-grant','book','LicenseRef-Source','PERMISSION','fixture-author',('terms-source',),**common,obligations=(Obligation('source-credit','ATTRIBUTION','Source: Diagnostic Author.'),))
    g2=Grant('asset-grant','diagram','LicenseRef-Asset','PERMISSION','fixture-artist',('terms-asset',),**common,obligations=(Obligation('asset-credit','CHANGE_NOTICE','Asset: Diagnostic Artist — modified.'),))
    reqs=(UseRequirement('source-use','book','lesson',('ADAPT','DISPLAY','DISTRIBUTE'),'LicenseRef-Output',('credits',)),
        UseRequirement('asset-use','diagram','lesson',('ADAPT','DISPLAY','DISTRIBUTE'),'LicenseRef-Output',('credits',)))
    policy=RightsPolicy('rights-policy',snap.content_digest,'bie-fixture',('IN',),('WEB',),True,NOW,NOW+100,(source,asset),(g1,g2),reqs)
    credits=blobs['credits'][1];selections=[]
    for uid,g in zip(('source-use','asset-use'),(g1,g2)):
        o=g.obligations[0];s=credits.index(o.required_text.encode());selections.append(UseSelection(uid,(g.grant_id,),(NoticeProof(g.grant_id,o.obligation_id,'credits',s,s+len(o.required_text.encode())),)))
    return RightsRequest('rights-job',snap,'rights-status',tuple(selections)),policy

def reviews_for(request,policy,*,key=KEY,verdict='VERIFIED',confidence=1000000):
    out=[]
    for i,((purpose,subject),ids) in enumerate(sorted(review_targets(request,policy).items())):
        r=Review('fixture-review-'+str(i),request.content_digest,policy.content_digest,subject,purpose,verdict,ids,confidence,
            'SYNTHETIC fixture approval, not an assessment of actual legal rights.',key.evaluator_id,key.evaluator_version,NOW-1,NOW+100,key.key_id)
        out.append(replace(r,signature=hmac.new(key.secret,r.signing_bytes(),hashlib.sha256).hexdigest()))
    return tuple(out)

def run(request,root,policy,*,signed=True,reviews=None,verifier=None,as_of=NOW):
    rs=reviews_for(request,policy) if signed else ()
    if reviews is not None:rs=reviews
    return evaluate(request,root,policy,as_of=as_of,reviews=rs,verifier=ReviewVerifier((KEY,)) if verifier is None else verifier)

def replace_blob(request,policy,root,aid,data):
    arts=[]
    for a in request.snapshot.artifacts:
        if a.artifact_id==aid:
            (Path(root)/a.path).write_bytes(data);a=replace(a,sha256=hashlib.sha256(data).hexdigest(),size=len(data))
        arts.append(a)
    snap=replace(request.snapshot,artifacts=tuple(arts));return replace(request,snapshot=snap),replace(policy,snapshot_digest=snap.content_digest)

def codes(result):return {f.code for r in result.reports for f in r.findings}

def release_fixture(root):
    request,policy=make_fixture(root);arts=list(request.snapshot.artifacts)
    for aid,role in [('video','video'),('game','game')]:
        data=('SYNTHETIC '+role+' placeholder for release-interface tests; not actual media.').encode();path='generated/'+aid+'.bin'
        (Path(root)/path).write_bytes(data);arts.append(ArtifactRef(aid,path,hashlib.sha256(data).hexdigest(),len(data),role))
    snap=replace(request.snapshot,artifacts=tuple(sorted(arts,key=lambda a:a.artifact_id)))
    us=[];ss=[]
    for aid in ('video','game'):
        for u,s in zip(policy.requirements,request.selections):
            uid=u.use_id+'-'+aid;us.append(replace(u,use_id=uid,output_artifact_id=aid));ss.append(replace(s,use_id=uid))
    return replace(request,snapshot=snap,selections=tuple(ss)),replace(policy,snapshot_digest=snap.content_digest,requirements=tuple(us))
