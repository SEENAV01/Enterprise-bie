"""Write-token job: inspect Git data only; never execute integrated project code."""
from __future__ import annotations
import argparse, base64, hashlib, json, os, re, subprocess
from pathlib import Path
BASE='73840d86a78e5f31438e2a1bad34f3b2a8433eb9'
CAPSULE_SHA='17ce2d9700ccb6227a7fb86a879a5f39c4e5ebec535980a7cdf446a2e961d9b4'
PLAN_SHA='63a2596d48b75bf4d9d16d5dd95635b6b557990f3a62b804899e5581e1eb81de'
BRANCH='integration/post-dir-catchup-20260919'

def h(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def command(root,*args,env=None):
    return subprocess.check_output(['git','-C',str(root),'-c','core.hooksPath=/dev/null',*args],env=env).decode().strip()
def tree(root,ref):
    out={}
    for row in subprocess.check_output(['git','-C',str(root),'ls-tree','-r','-z',ref]).split(b'\0'):
        if not row:continue
        info,path=row.split(b'\t',1);mode,kind,key=info.decode().split()
        out[path.decode()]=(mode,kind,key)
    return out

def verify_commit_chain(root,trigger,candidate,plan):
    commits=command(root,'rev-list','--reverse',trigger+'..'+candidate).splitlines()
    if len(commits)!=4 or [p['section'] for p in plan['phases']]!=['VIS','ANI','DSL','COMP']:
        raise ValueError('WRONG_COMMIT_CHAIN')
    previous=trigger;expected=tree(root,trigger)
    for commit,phase in zip(commits,plan['phases']):
        if command(root,'show','-s','--format=%P',commit)!=previous:raise ValueError('NONLINEAR_HISTORY')
        actual=tree(root,commit)
        for row in phase['operations']:expected[row['path']]=(row['mode'],'blob',row['git_blob_sha1'])
        if actual!=expected:raise ValueError('UNDECLARED_OR_INCORRECT_TREE_CHANGE:'+phase['section'])
        previous=commit
    return commits

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--artifact',type=Path,required=True)
    p.add_argument('--trigger',required=True);p.add_argument('--bundle-sha',required=True);p.add_argument('--receipt-sha',required=True)
    p.add_argument('--candidate',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=a.root.resolve();data=a.artifact.resolve()
    for name in ('adoption.bundle','plan.json','receipt.json'):
        if not (data/name).is_file() or (data/name).is_symlink():raise ValueError('ARTIFACT_FILE_INVALID')
    if h(data/'adoption.bundle')!=a.bundle_sha or h(data/'receipt.json')!=a.receipt_sha or h(data/'plan.json')!=PLAN_SHA:
        raise ValueError('ARTIFACT_IDENTITY_MISMATCH')
    receipt=json.loads((data/'receipt.json').read_text());plan=json.loads((data/'plan.json').read_text())
    required={'base_commit':BASE,'trigger_commit':a.trigger,'candidate_commit':a.candidate,
              'bundle_sha256':a.bundle_sha,'capsule_sha256':CAPSULE_SHA,'plan_sha256':PLAN_SHA,
              'product_accepted':False,'runtime_accepted':False}
    if any(receipt.get(k)!=v for k,v in required.items()):raise ValueError('RECEIPT_BINDING_MISMATCH')
    t=receipt['tests'];s=receipt['preservation']
    if t.get('passed') is not True or t.get('tests_run')!=6485 or any(t.get(k)!=0 for k in ('failures','errors','skipped','failed_files')):
        raise ValueError('REGRESSION_NOT_VERIFIED')
    if s.get('passed') is not True or s.get('supplied_files_verified')!=386 or s.get('errors')!=[]:
        raise ValueError('PRESERVATION_NOT_VERIFIED')
    if command(root,'rev-parse','HEAD')!=a.trigger or command(root,'status','--porcelain'):
        raise ValueError('PUBLISH_CHECKOUT_CHANGED')
    if command(root,'remote','get-url','origin') not in ('https://github.com/SEENAV01/Enterprise-bie','https://github.com/SEENAV01/Enterprise-bie.git'):
        raise ValueError('UNEXPECTED_REMOTE')
    command(root,'bundle','verify',str(data/'adoption.bundle'))
    command(root,'-c','fetch.fsckObjects=true','fetch',str(data/'adoption.bundle'),'HEAD:refs/integration-verified/candidate')
    if command(root,'rev-parse','refs/integration-verified/candidate')!=a.candidate:raise ValueError('BUNDLE_HEAD_MISMATCH')
    verify_commit_chain(root,a.trigger,a.candidate,plan)
    token=os.environ.get('GH_TOKEN')
    if not token:raise ValueError('WRITE_TOKEN_UNAVAILABLE')
    env=dict(os.environ);env.update({'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'http.https://github.com/.extraheader',
        'GIT_CONFIG_VALUE_0':'AUTHORIZATION: basic '+base64.b64encode(('x-access-token:'+token).encode()).decode()})
    remote=command(root,'ls-remote','origin','refs/heads/'+BRANCH,env=env).split()
    mainref=command(root,'ls-remote','origin','refs/heads/main',env=env).split()
    if not remote or remote[0]!=a.trigger:raise ValueError('STAGING_ADVANCED_REVIEW_REQUIRED')
    if not mainref or mainref[0]!=BASE:raise ValueError('MAIN_ADVANCED_REVIEW_REQUIRED')
    command(root,'checkout','--detach',a.candidate)
    receipt['publication_scope']='STAGING_ONLY; main requires separate readback/review.'
    receipt['workflow_url']='https://github.com/SEENAV01/Enterprise-bie/actions/runs/'+os.environ['GITHUB_RUN_ID']
    target=root/'docs/evidence/post-dir-integration/REMOTE_VALIDATION.json'
    if target.exists():raise ValueError('RECEIPT_COLLISION')
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(receipt,indent=2)+'\n')
    command(root,'config','user.name','BIE Canonical Integration');command(root,'config','user.email','actions@users.noreply.github.com')
    command(root,'--literal-pathspecs','add','-f',str(target.relative_to(root)))
    command(root,'commit','-m','chore: record verified post-DIR source integration [canonical-integration]')
    final=command(root,'rev-parse','HEAD')
    command(root,'push','origin','HEAD:refs/heads/'+BRANCH,env=env)
    readback=command(root,'ls-remote','origin','refs/heads/'+BRANCH,env=env).split()[0]
    if readback!=final:raise ValueError('REMOTE_READBACK_MISMATCH')
    result={'published':True,'branch':BRANCH,'commit':final,'tree':command(root,'rev-parse','HEAD^{tree}'),
            'main_unchanged':command(root,'ls-remote','origin','refs/heads/main',env=env).split()[0]==BASE,
            'source_candidate':a.candidate,'capsule_sha256':CAPSULE_SHA,'product_accepted':False}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
