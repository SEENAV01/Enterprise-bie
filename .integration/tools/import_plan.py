"""Apply a sealed data-only plan; never recover code by interpreting summaries.

Use inside the repository checked out at the triggering commit. This tool does
not push Git refs. Publication is a separate gated job with separate permissions.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, tempfile
from pathlib import Path, PurePosixPath
from restore_capsule import unpack_capsule, restore
HEX=re.compile(r'^[0-9a-f]{64}$')
BASE='73840d86a78e5f31438e2a1bad34f3b2a8433eb9'
ALLOWED=('bie/','tests/','scripts/','docs/','backups/','manifests/','task_registry/','fixtures/','validation/','lineage/','original_archives/','source_artifacts/','examples/','governance/')
ROOT_NAMES={'README.md','BIE_CONTEXT_HANDOFF.md','CONTINUATION.json','BATCH_MANIFEST.json','WORKSPACE_SHA256SUMS.txt'}

def sha(b):return hashlib.sha256(b).hexdigest()
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()

def allowed_path(value):
    if not isinstance(value,str) or not value or '\\' in value or '\0' in value:raise ValueError('INVALID_PATH')
    p=PurePosixPath(value)
    if p.as_posix()!=value or p.is_absolute() or '..' in p.parts or '.' in p.parts or '.git' in p.parts:raise ValueError('PATH_ESCAPE')
    if not (value.startswith(ALLOWED) or '/' not in value and (value in ROOT_NAMES or value.startswith(('BIE_','README_','requirements-','ARCHIVE_','DELIVERY_','SOURCE_','TASK_','TEST_','CANONICAL_','INTEGRATION_')))):
        raise ValueError('UNAPPROVED_DESTINATION:'+value)
    return value

def preflight_plan(root, plan, object_root):
    if plan.get('schema_version')!='bie.canonical-adoption-plan.v1' or plan.get('base_commit')!=BASE:raise ValueError('PLAN_BASE')
    if [p['section'] for p in plan['phases']]!=['VIS','ANI','DSL','COMP']:raise ValueError('PLAN_ORDER')
    state={};count=0
    for phase in plan['phases']:
        within=set()
        for item in phase['operations']:
            name=allowed_path(item['path']);key=item['sha256'];old=item['before_sha256'];count+=1
            if name in within:raise ValueError('DUPLICATE_PHASE_PATH')
            within.add(name)
            if count>30000 or not HEX.fullmatch(key) or old is not None and not HEX.fullmatch(old):raise ValueError('PLAN_HASH_OR_BUDGET')
            p=root/name
            if any(x.is_symlink() for x in (p,*p.parents)):raise ValueError('SYMLINK_DESTINATION')
            if p.exists() and not p.is_file():raise ValueError('NONREGULAR_DESTINATION')
            actual=state.get(name, sha(p.read_bytes()) if p.is_file() else None)
            if actual!=old:raise ValueError('BASE_COLLISION:'+name)
            source=object_root/key
            if source.is_symlink() or not source.is_file():raise ValueError('MISSING_OBJECT')
            data=source.read_bytes()
            if sha(data)!=key or len(data)!=item['bytes'] or item['mode'] not in ('100644','100755'):raise ValueError('OBJECT_IDENTITY')
            state[name]=key
    if count!=plan['operation_count']:raise ValueError('OPERATION_COUNT')
    return state

def verify_tree(root, commit, plan):
    final={}
    for phase in plan['phases']:
        for item in phase['operations']:final[item['path']]=item
    entries={}
    raw=subprocess.check_output(['git','-C',str(root),'ls-tree','-r','-z',commit])
    for row in raw.split(b'\0'):
        if not row:continue
        header,name=row.split(b'\t',1);mode,typ,key=header.decode().split();entries[name.decode()]=(mode,typ,key)
    for name,item in final.items():
        if entries.get(name)!=(item['mode'],'blob',item['git_blob_sha1']):raise ValueError('COMMITTED_BLOB_MISMATCH:'+name)
    return len(final)

def apply(root, extracted, restored, *, create_commits=True):
    plan=json.loads((extracted/'plan.json').read_text());objects=restored/'objects'
    preflight_plan(root,plan,objects)
    commits=[]
    for phase in plan['phases']:
        paths=[]
        for item in phase['operations']:
            p=root/item['path'];p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('wb') as f:f.write((objects/item['sha256']).read_bytes())
            p.chmod(0o755 if item['mode']=='100755' else 0o644)
            paths.append(item['path'])
        if create_commits and paths:
            with tempfile.NamedTemporaryFile() as f:
                f.write(b'\0'.join(p.encode() for p in paths)+b'\0');f.flush()
                git(root,'--literal-pathspecs','add','-f','--pathspec-from-file='+f.name,'--pathspec-file-nul')
            git(root,'-c','core.hooksPath=/dev/null','commit','-m',f"feat({phase['section'].lower()}): exact-source canonical adoption; combined gate pending [canonical-integration]")
            commits.append({'section':phase['section'],'commit':git(root,'rev-parse','HEAD')})
    if create_commits:verify_tree(root,'HEAD',plan)
    return {'phases':commits,'operation_count':plan['operation_count'],'supplied_files':plan['supplied_files'],'accepted':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('payload',type=Path);p.add_argument('--sha256',required=True);p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--work',type=Path,required=True);a=p.parse_args()
    root=a.root.resolve();a.work.mkdir(parents=True,exist_ok=False)
    subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',BASE,'HEAD'],check=True)
    for path in git(root,'diff','--name-only',BASE,'HEAD').splitlines():
        if not path.startswith(('.integration/','.github/','docs/evidence/post-dir-catchup-20260919/')):raise ValueError('UNEXPECTED_STAGING_CHANGE:'+path)
    if git(root,'status','--porcelain'):raise ValueError('DIRTY_CHECKOUT')
    git(root,'config','core.autocrlf','false');git(root,'config','user.name','BIE Canonical Integration');git(root,'config','user.email','actions@users.noreply.github.com')
    unpack_capsule(a.payload,a.work/'capsule',a.sha256)
    restore(a.work/'capsule',a.work/'restored')
    result=apply(root,a.work/'capsule',a.work/'restored')
    (a.work/'APPLIED.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
