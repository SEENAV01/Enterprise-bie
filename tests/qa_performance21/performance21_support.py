"""Explicitly SYNTHETIC authorization and timing records for adversarial unit tests."""
from pathlib import Path
from dataclasses import replace,asdict
import hashlib,hmac,sys
from bie.qa.release_v2.contracts import ArtifactRef,canonical_bytes,digest
from bie.qa.repair_v2.models import Snapshot
from bie.qa.performance_v2 import *
from bie.qa.performance_v2.evaluator import PROFILE,MEMORY_BASIS,file_hash,review_targets
from bie.qa.reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier
NOW=10000
KEY=ReviewKey('perf-synthetic',b'PERF21-SYNTHETIC-FIXTURE-KEY-NOT-REAL-AUTHORITY','perf-fixture','1','test-group',('inventory','support'),'operator_managed')

def ref(root,aid,path,data,role='support'):
    p=Path(root)/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    return ArtifactRef(aid,path,hashlib.sha256(data).hexdigest(),len(data),role)

def fixture(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    snap=Snapshot('perf-test','a'*40,(ref(root,'source','source/book.txt',b'AUTHORED DIAGNOSTIC NOT A BOOK','source'),
        ref(root,'video','candidate/video.bin',b'SYNTHETIC VIDEO PLACEHOLDER','video'),ref(root,'game','candidate/game.bin',b'SYNTHETIC GAME PLACEHOLDER','game')))
    o=OutputSpec('result','outputs/result.bin','BYTES',hashlib.sha256(b'hello').hexdigest())
    jobs=(JobSpec('first','producer',('source',),(o,)),JobSpec('second','producer',('source',),(o,)))
    env={'fixture':'SYNTHETIC ENVIRONMENT'}
    policy=PerformancePolicy('perf-policy',snap.content_digest,jobs,(('producer','b'*64),),digest(env))
    ev=[];eid='perf-'+'1'*32
    def add(aid,name,data,role='report'):
        a=ref(root,aid,'evidence/'+name,data,role);ev.append(a);return aid
    def process(jid,pid,a,b,c,d,e):
        std=canonical_bytes({'schema_version':'bie.qa.performance-memory-probe/1','positive_allocation':True,'over_limit_denied':True,'address_space_limit':policy.address_space_bytes,'rss_limit_tested':False}) if jid=='memoryprobe' else b''
        limits=dict(schema_version='bie.qa.performance-limits/1',execution_id=eid+'-'+jid,address_space=[policy.address_space_bytes]*2,file_size=[policy.max_file_bytes]*2,cpu=[(policy.timeout_ms+999)//1000+1]*2,nofile=[64,64],memory_scope='RLIMIT_AS_PER_PROCESS_NOT_RSS_OR_CGROUP')
        outputs={} if jid=='memoryprobe' else {'result':add(jid+'-result',jid+'/result.bin',b'hello','support')}
        return dict(job_id=jid,producer_id=pid,execution_id=eid+'-'+jid,enqueue_ns=a,dispatch_ns=b,process_start_ns=c,process_end_ns=d,complete_ns=e,exit_code=0,timed_out=False,input_unchanged=True,peak_rss_bytes=30*1024**2,cpu_user_ns=1000000,cpu_system_ns=1000000,memory_basis=MEMORY_BASIS,
            stdout_id=add(jid+'-stdout',jid+'/stdout.json',canonical_bytes({'encoding':'hex','data':std.hex()})),
            stderr_id=add(jid+'-stderr',jid+'/stderr.json',canonical_bytes({'encoding':'hex','data':''})),
            limits_id=add(jid+'-limits',jid+'/limits.json',canonical_bytes(limits)),outputs=outputs,issues=[])
    probe=process('memoryprobe','bundled-memory-probe',0,0,1,4000000,5000000)
    rows=[process('first','producer',10000000,11000000,12000000,30000000,40000000),process('second','producer',10000000,20000000,21000000,49000000,50000000)]
    raw=dict(schema_version='bie.qa.performance-execution/1',execution_id=eid,snapshot_digest=snap.content_digest,policy_digest=policy.content_digest,started_at=NOW-2,finished_at=NOW-1,profile=PROFILE,environment_before=env,environment_after=env,collector_sha256=file_hash('collector.py'),launcher_sha256=file_hash('limit_exec.py'),probe_sha256=file_hash('memory_probe.py'),producers=[list(x) for x in policy.producer_bindings],queue_start_ns=10000000,queue_end_ns=50000000,jobs=rows,memory_probe=probe,product_accepted=False,native_queue_executed=False)
    rid=add('receipt','execution.json',canonical_bytes(raw))
    return PerformanceRequest(snap,tuple(ev),rid),policy,raw

def rewrite(request,root,aid,data):
    refs=[]
    for a in request.evidence:
        if a.artifact_id==aid:a=ref(root,a.artifact_id,a.path,data,a.role)
        refs.append(a)
    return replace(request,evidence=tuple(refs))

def rebind(request,root,raw):return rewrite(request,root,request.receipt_id,canonical_bytes(raw))

def signed(r,p,key=KEY,verdict='VERIFIED'):
    rows=[]
    for i,((purpose,subject),ids) in enumerate(sorted(review_targets(r,p).items())):
        row=Review('perf-review-'+str(i),r.content_digest,p.content_digest,subject,purpose,verdict,ids,1000000,'SYNTHETIC review fixture; not real measurement attestation.',key.evaluator_id,key.evaluator_version,NOW-1,NOW+60,key.key_id)
        rows.append(replace(row,signature=hmac.new(key.secret,row.signing_bytes(),hashlib.sha256).hexdigest()))
    return tuple(rows)

def run(r,root,p,*,reviews=None,verifier=None,as_of=NOW):
    return evaluate(r,root,p,as_of=as_of,reviews=signed(r,p) if reviews is None else reviews,verifier=ReviewVerifier((KEY,)) if verifier is None else verifier)

def codes(result):return {f.code for r in result.reports for f in r.findings}

def real_fixture(root,body=None,jobs=2):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    body=body or b'import sys\nfrom pathlib import Path\nPath(sys.argv[1]).write_bytes(b"hello")\n'
    snap=Snapshot('real-perf','a'*40,(ref(root,'worker','source/worker.py',body),))
    exe=Path(getattr(sys,'_base_executable',sys.executable)).resolve()
    producer=Producer('python',str(exe),hashlib.sha256(exe.read_bytes()).hexdigest(),('-I','-B','-S','{input:worker}','{output:result}'))
    output=OutputSpec('result','outputs/result.bin','BYTES',hashlib.sha256(b'hello').hexdigest())
    specs=tuple(JobSpec('job'+str(i),'python',('worker',),(output,)) for i in range(jobs))
    p=PerformancePolicy('real-policy',snap.content_digest,specs,((producer.producer_id,producer.content_digest),),digest(capture_environment()))
    return PerformanceRequest(snap),p,(producer,)
