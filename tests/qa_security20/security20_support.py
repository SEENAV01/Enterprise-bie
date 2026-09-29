"""Synthetic credentials and sandbox receipts; never operational security attestation."""
from pathlib import Path
from dataclasses import asdict,replace
import errno,hashlib,hmac,json,shutil
from bie.qa.release_v2.contracts import ArtifactRef,canonical_bytes
from bie.qa.repair_v2.models import Snapshot
from bie.qa.security_v2 import *
from bie.qa.reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier
NOW=10000
KEY=ReviewKey('synthetic-sec-key',b'SYNTHETIC-SEC-020-FIXTURE-ONLY-NOT-AUTHORITY','fixture-security','1','fixture-group',('inventory','support'),'operator_managed')

def tools():
    node=Path(shutil.which('node')).resolve();tsc=Path(shutil.which('tsc')).resolve();ts=tsc.parent.parent/'lib/typescript.js'
    return Toolchain(str(node),hashlib.sha256(node.read_bytes()).hexdigest(),str(ts),hashlib.sha256(ts.read_bytes()).hexdigest())

def synthetic_receipt(snapshot_digest):
    import bie.qa.security_v2.boundary_worker as w
    obs=[];processes=[]
    for j,case in enumerate(('standard','file_limit','descriptor_limit')):
        rows=[]
        for name in (PROBES[:-2] if case=='standard' else (case,)):
            if name.startswith('allowed_'):a,b,e='ALLOW','ALLOWED',0
            elif name=='environment':a,b,e='ABSENT','ABSENT',0
            else:a,b,e='DENY','DENIED',{'inherited_fd':errno.EBADF,'file_limit':errno.EFBIG,'descriptor_limit':errno.EMFILE}.get(name,errno.EPERM)
            rows.append(dict(probe=name,expected=a,observed=b,errno=e,passed=True))
        child=dict(schema_version='bie.qa.boundary-child/1',case=case,nonce=str(j+1)*32,code_executed=False,profile='LINUX_CHROOT_SECCOMP_FIXED_PROBES_V1',controls={c:True for c in CONTROLS},observations=rows,status='CHECKS_PASSED')
        stdout=canonical_bytes(child).decode();processes.append(dict(case=case,execution_id='sec-synthetic-'+case,exit_code=0,elapsed_ms=5,stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(b'').hexdigest(),stdout=stdout,stderr='',receipt=child));obs+=rows
    return dict(schema_version='bie.qa.sandbox-diagnostics/1',execution_id='sec-synthetic',snapshot_digest=snapshot_digest,started_at=NOW-2,finished_at=NOW-1,worker_sha256=hashlib.sha256(Path(w.__file__).read_bytes()).hexdigest(),interpreter_sha256='a'*64,profile='LINUX_CHROOT_SECCOMP_FIXED_PROBES_V1',platform='SYNTHETIC FIXTURE',processes=processes,observations=obs,outside_canary_unchanged=True,status='CHECKS_PASSED',candidate_executed=False,product_accepted=False)

def ref(root,aid,path,b,role='support'):
    p=Path(root)/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    return ArtifactRef(aid,path,hashlib.sha256(b).hexdigest(),len(b),role)

def fixture(root,language='PYTHON',profile='PURE',code=None,receipt=True):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    code=code if code is not None else b'def add(a, b):\n    return a + b\n'
    ext={'PYTHON':'py','TYPESCRIPT':'ts','TSX':'tsx','JAVASCRIPT':'js','NPM_MANIFEST':'json'}[language]
    path='generated/package.json' if language=='NPM_MANIFEST' else 'generated/unit.'+ext
    arts=(ref(root,'code',path,code),ref(root,'source','source/lesson.txt',b'AUTHORED DIAGNOSTIC NOT A BOOK','source'),ref(root,'video','generated/video.bin',b'SYNTHETIC VIDEO PLACEHOLDER','video'),ref(root,'game','generated/game.bin',b'SYNTHETIC GAME PLACEHOLDER','game'))
    snap=Snapshot('sec-run','a'*40,arts);r=SecurityRequest(snap)
    t=tools() if language in ('TYPESCRIPT','TSX','JAVASCRIPT') else None
    p=SecurityPolicy('sec-policy',snap.content_digest,(CodeUnit('code',language,profile),),parser_node_sha256=t.node_sha256 if t else '',parser_typescript_sha256=t.typescript_sha256 if t else '')
    if receipt:r=attach(r,root,synthetic_receipt(snap.content_digest))
    return r,p,t

def attach(r,root,raw):
    return replace(r,sandbox_evidence=ref(root,'sandbox','evidence/boundary.json',canonical_bytes(raw),'report'))

def rewrite_child(raw,index,fn):
    child=raw['processes'][index]['receipt'];fn(child)
    raw['processes'][index]['stdout']=canonical_bytes(child).decode();raw['processes'][index]['stdout_sha256']=hashlib.sha256(raw['processes'][index]['stdout'].encode()).hexdigest()
    raw['observations']=[x for p in raw['processes'] for x in p['receipt']['observations']]
    return raw

def signed(r,p,key=KEY,verdict='VERIFIED'):
    out=[]
    for i,((purpose,subject),ids) in enumerate(sorted(review_targets(r,p).items())):
        row=Review('review-'+str(i),r.content_digest,p.content_digest,subject,purpose,verdict,ids,1000000,'SYNTHETIC approval only; not operational security review.',key.evaluator_id,key.evaluator_version,NOW-1,NOW+60,key.key_id)
        out.append(replace(row,signature=hmac.new(key.secret,row.signing_bytes(),hashlib.sha256).hexdigest()))
    return tuple(out)

def run(r,root,p,t=None,*,reviews=None,verifier=None,as_of=NOW):
    return evaluate(r,root,p,as_of=as_of,reviews=signed(r,p) if reviews is None else reviews,verifier=ReviewVerifier((KEY,)) if verifier is None else verifier,toolchain=t)

def codes(result):return {f.code for r in result.reports for f in r.findings}
