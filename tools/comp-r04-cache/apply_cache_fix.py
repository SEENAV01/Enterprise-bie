#!/usr/bin/env python3
"""Correct reproduced cache EROFS and both active-target ledger views. No main write."""
from __future__ import annotations
import argparse, base64, copy, hashlib, importlib.util, io, json, os, re, subprocess, sys, unittest
from pathlib import Path

HELPER=Path(__file__).resolve().parents[1]/'comp-r04-fix/apply_capture_fix.py'
data=HELPER.read_bytes()
if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!='3f20b776375128cf6c3aa00abf102f6df192e4a7':
    raise SystemExit('REVIEWED_SOURCE_PUBLISHER_CHANGED')
spec=importlib.util.spec_from_file_location('r04_guard',HELPER);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
require,sha,blob,save,git,request=base.require,base.sha,base.blob,base.save,base.git,base.request
SOURCE='bie/compiler/qa_support/remotion_raster_capture.cjs'
ORIGINAL_BLOB='f1af451633b8b2a414429e7971726b4b2aa0d7a6'
MANIFEST='manifests/post_dir_integration_004.json'
PRIOR_MANIFEST_BLOB='f99aa66205f5e233e407a4129b29d7177fbb420c'
PRIOR_SOURCE='76b6f6da0cde70413f34ad4521f931fb0eb02a2d'
PY_OLD='fc320220631020b0bc246786e659ea105313e11b6a47ef97b99db6ed043e07bf'
PY_NEW='ab939ee47dc3b4aed58aceab72db8ebdb5d3c42cab77c329ced8630b03f72a86'
TEST='tests/compiler/test_r04_capture_cache.py'
NOTE='docs/evidence/comp-r04-capture-cache'
OLD=" const serveUrl=await bundle({entryPoint:path.join(req.workspace,'qa-capture-entry.tsx'),outDir:path.join(out,'bundle'),publicDir:path.join(req.workspace,'public')});\n"
NEW=" // Source and dependencies are immutable in the isolated capture worker.\n // Do not let Webpack create or invalidate a cache under node_modules.\n"+OLD.replace("bundle({entryPoint:","bundle({enableCaching:false,entryPoint:")


def tests(root,out,passed):
    spec=importlib.util.spec_from_file_location('capture_cache_test',root/TEST);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    result={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),'passed':r.wasSuccessful(),'scope':'ACTUAL_BUNDLE_OPTIONS_ONLY_NOT_RENDER','accepted':False,'log':stream.getvalue()}
    save(out,result)
    require(r.testsRun==5 and not r.skipped,'CONFIGURATION_TEST_SET_CHANGED')
    require(r.wasSuccessful() if passed else len(r.failures)==1 and not r.errors,'UNEXPECTED_CACHE_CONFIGURATION_TEST_RESULT')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',required=True,type=Path);p.add_argument('--evidence',required=True,type=Path);p.add_argument('--expected-parent',required=True);p.add_argument('--publish-review-branch',action='store_true')
    a=p.parse_args();root=a.repo.resolve();out=a.evidence.resolve();require(not out.is_relative_to(root),'EXTERNAL_EVIDENCE_REQUIRED');out.mkdir(parents=True,exist_ok=False)
    require(git(root,'rev-parse','HEAD')==a.expected_parent,'WRONG_PARENT');require(not git(root,'status','--porcelain','--untracked-files=all'),'UNCLEAN_SOURCE')
    require(request('GET','/git/ref/heads/'+base.BRANCH)['object']['sha']==a.expected_parent,'REVIEW_BRANCH_MOVED')
    require(request('GET','/git/ref/heads/main')['object']['sha']==base.MAIN,'MAIN_MOVED')
    before=(root/SOURCE).read_bytes();raw=(root/MANIFEST).read_bytes()
    require(blob(before)==ORIGINAL_BLOB and before.count(OLD.encode())==1,'CAPTURE_SOURCE_CHANGED')
    require(blob(raw)==PRIOR_MANIFEST_BLOB,'LEDGER_CHANGED')
    require(sha((root/base.SOURCE).read_bytes())==PY_NEW,'FIRST_COVERAGE_FIX_CHANGED')
    require(not (root/TEST).exists() and not (root/NOTE).exists(),'CACHE_CANDIDATE_ALREADY_EXISTS')
    (root/TEST).write_bytes(Path(__file__).with_name('test_cache_configuration.py').read_bytes())
    tests(root,out/'ORIGINAL_CACHE_CONFIG_TESTS.json',False)
    after=before.replace(OLD.encode(),NEW.encode());(root/SOURCE).write_bytes(after)
    tests(root,out/'CANDIDATE_CACHE_CONFIG_TESTS.json',True)
    old=json.loads(raw);require((json.dumps(old,indent=2,sort_keys=True)+'\n').encode()==raw,'LEDGER_FORMAT_CHANGED')
    updated=copy.deepcopy(old);changes=[]
    for group in ('members','source_members'):
        for index,row in enumerate(updated[group]):
            path=row.get('canonical_path')
            if path not in (SOURCE,base.SOURCE):continue
            expected=sha(after) if path==SOURCE else PY_NEW
            prior=row['canonical_sha256'];require(prior in ({sha(before)} if path==SOURCE else {PY_OLD,PY_NEW}),'UNEXPECTED_ACTIVE_HASH')
            if prior!=expected:
                row['canonical_sha256']=expected;changes.append({'group':group,'index':index,'path':path,'field':'canonical_sha256','before':prior,'after':expected})
            if path==SOURCE:
                key='transformation' if group=='members' else 'disposition'
                require(row[key]=='BYTE_IDENTICAL_ADOPTION','UNEXPECTED_ORIGINAL_DISPOSITION')
                row[key]='CANONICAL_PATH_ADAPTATION_OR_DOCUMENTED_AMENDMENT'
                changes.append({'group':group,'index':index,'path':path,'field':key,'before':'BYTE_IDENTICAL_ADOPTION','after':row[key]})
    require(len(changes)==5,'UNEXPECTED_LEDGER_CHANGE_COUNT')
    revised=(json.dumps(updated,indent=2,sort_keys=True)+'\n').encode();(root/MANIFEST).write_bytes(revised)
    note=root/NOTE;note.mkdir(parents=True);(note/'original-remotion_raster_capture.cjs.txt').write_bytes(before)
    receipt={'schema_version':'bie.r04.cache-and-target-adaptation.v1','parent_commit':a.expected_parent,'prior_source_commit':PRIOR_SOURCE,'source_path':SOURCE,'source_before_git_blob':blob(before),'source_after_git_blob':blob(after),'source_before_sha256':sha(before),'source_after_sha256':sha(after),'manifest_path':MANIFEST,'manifest_before_git_blob':blob(raw),'manifest_after_git_blob':blob(revised),'manifest_before_sha256':sha(raw),'manifest_after_sha256':sha(revised),'manifest_before_image':{'commit':PRIOR_SOURCE,'path':MANIFEST,'git_blob':PRIOR_MANIFEST_BLOB},'ledger_changes':changes,'original_archive_and_member_hashes_changed':False,'source_delta':{'before':OLD,'after':NEW},'reproduced_runtime_failure_run':35499934225,'reproduced_runtime_failure':'EROFS: node_modules/.cache/webpack/remotion-production-4.0.506','scope':'Disable optional bundle caching while keeping source/dependency mounts immutable; align both active canonical-target views','cache_contract_tests':5,'guard_and_isolation_code_changed':False,'real_render_status':'NOT_RUN_AT_COMMIT','accepted':False}
    save(note/'SOURCE_ADAPTATION.json',receipt)
    changed=[SOURCE,MANIFEST,TEST,NOTE+'/original-remotion_raster_capture.cjs.txt',NOTE+'/SOURCE_ADAPTATION.json']
    for name,cmd in [('assembly',['scripts/verify_assembly.py']),('canonical',['scripts/audit_canonical.py','--output',str(out/'CANONICAL_PRESERVATION.json')]),('ingested',['scripts/verify_ingested_archives.py','--output',str(out/'INGESTED_PRESERVATION.json')]),('post-dir',['scripts/verify_post_dir.py','--output',str(out/'POST_DIR_PRESERVATION.json')])]:
        r=subprocess.run([sys.executable,'-B',*cmd],cwd=root,capture_output=True,text=True,timeout=300);(out/(name+'.log')).write_text(r.stdout+r.stderr);require(r.returncode==0,'PRESERVATION_FAILED:'+name)
    git(root,'add','--',*changed);require(set(git(root,'diff','--cached','--name-only').splitlines())==set(changed),'UNEXPECTED_STAGED_FILE')
    (out/'SOURCE_CANDIDATE.patch').write_text(git(root,'diff','--cached','--binary')+'\n');tree=git(root,'write-tree')
    result={'parent_commit':a.expected_parent,'source_tree':tree,'changed_files':changed,'published':False,'accepted':False}
    if a.publish_review_branch:
        require(request('GET','/git/ref/heads/'+base.BRANCH)['object']['sha']==a.expected_parent,'REVIEW_BRANCH_MOVED_BEFORE_PUBLISH')
        token=os.environ.get('GH_TOKEN');require(bool(token),'TOKEN_REQUIRED')
        env=dict(os.environ,GIT_AUTHOR_NAME='BIE R04 validation',GIT_AUTHOR_EMAIL='noreply@users.noreply.github.com',GIT_COMMITTER_NAME='BIE R04 validation',GIT_COMMITTER_EMAIL='noreply@users.noreply.github.com')
        source_sha=subprocess.check_output(['git','commit-tree',tree,'-p',a.expected_parent],cwd=root,env=env,text=True,input='fix(comp): disable capture cache writes under immutable dependency mount\n\nReproduced EROFS in run 35499934225. Preserve original source and origin hashes; reconcile both active canonical-target views. Five focused cache contracts; all four unchanged preservation verifiers pass. No source-coverage, isolation, dependency or acceptance relaxation.\n').strip()
        require(re.fullmatch('[0-9a-f]{40}',source_sha) is not None,'INVALID_COMMIT')
        auth=base64.b64encode(('x-access-token:'+token).encode()).decode();env.update(GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',GIT_CONFIG_VALUE_0='AUTHORIZATION: basic '+auth,GIT_CONFIG_KEY_1='credential.helper',GIT_CONFIG_VALUE_1='',GIT_TERMINAL_PROMPT='0')
        r=subprocess.run(['git','push','https://github.com/'+base.REPO+'.git',source_sha+':refs/heads/'+base.BRANCH],cwd=root,env=env,capture_output=True,text=True,timeout=180,check=False)
        (out/'git-publication.log').write_text((r.stdout+r.stderr).replace(token,'[REDACTED]').replace(auth,'[REDACTED]'));require(r.returncode==0,'NONFORCED_PUBLICATION_FAILED')
        require(request('GET','/git/ref/heads/'+base.BRANCH)['object']['sha']==source_sha,'SOURCE_REF_MISMATCH');require(request('GET','/git/commits/'+source_sha)['tree']['sha']==tree,'TREE_MISMATCH');require(request('GET','/git/ref/heads/main')['object']['sha']==base.MAIN,'MAIN_CHANGED')
        result.update(source_sha=source_sha,published=True,branch=base.BRANCH)
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('source_sha='+source_sha+'\nsource_tree='+tree+'\n')
    save(out/'SOURCE_PUBLICATION.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
