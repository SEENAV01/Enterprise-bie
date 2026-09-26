#!/usr/bin/env python3
"""Apply one guarded source correction and publish only to the R04 review branch.

Never changes main, a source-coverage verifier, dependency pin, supplied archive,
historical result, or acceptance flag. Complete before-images are retained.
GitHub publication requires an explicit flag, token, exact parent, and branch.
"""
from __future__ import annotations
import argparse
import base64
import copy
import csv
import hashlib
import importlib.util
import io
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import unittest
import urllib.request

REPO = 'SEENAV01/Enterprise-bie'
BRANCH = 'validation/comp-r04-20260920'
MAIN = '16d4d87824e77db3565a231a332e7977d39d7117'
SOURCE = 'bie/compiler/real_paint.py'
SOURCE_BLOB = 'd5d076035ca375fa8fae91399c0f0cf1d41e02a2'
TEST = 'tests/compiler/test_r04_capture_coverage.py'
HISTORY = 'docs/evidence/comp-r04-capture-coverage'
LINE = "        stage_cfg['include']+=['qa-capture-entry.tsx','qa-paint-helper.js','qa-paint-helper.d.ts']\n"
ADDITION = ("        # A same-basename declaration may hide JS discovered only by include.\n"
            "        # Explicit membership retains executable-helper coverage and strict TS.\n"
            "        stage_cfg['files']=list(dict.fromkeys([*stage_cfg.get('files',[]),'qa-paint-helper.js']))\n")


def require(ok, message):
    if not ok: raise ValueError(message)


def sha(data): return hashlib.sha256(data).hexdigest()

def blob(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2); f.write('\n')


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def check_tests(root, output, expected_pass):
    spec=importlib.util.spec_from_file_location('r04_capture_unit', root/TEST)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    value={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
           'skips':len(result.skipped),'passed':result.wasSuccessful(),
           'scope':'ACTUAL_CAPTURE_CONFIGURATION_STATEMENTS_ONLY_NOT_RENDER', 'accepted':False,
           'log':stream.getvalue()}
    save(output, value)
    require(result.testsRun==8 and not result.skipped, 'FOCUSED_TEST_DISCOVERY_CHANGED')
    if expected_pass:
        require(result.wasSuccessful(), 'FOCUSED_CANDIDATE_TESTS_FAILED')
    else:
        require(len(result.failures)==1 and len(result.errors)==1, 'EXPECTED_ORIGINAL_DEFECT_NOT_REPRODUCED')
        require('KeyError: \'files\'' in stream.getvalue(), 'WRONG_ORIGINAL_FAILURE')


def request(method, path, payload=None):
    token=os.environ.get('GH_TOKEN')
    require(bool(token), 'EXPLICIT_GITHUB_TOKEN_REQUIRED')
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request('https://api.github.com/repos/'+REPO+path, data=data, method=method,
        headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json',
                 'X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=120) as response:
        raw=response.read(); return json.loads(raw) if raw else {}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--expected-parent', required=True)
    p.add_argument('--publish-review-branch', action='store_true')
    a=p.parse_args(); root=a.repo.resolve(); out=a.evidence.resolve()
    require(not out.is_relative_to(root), 'EVIDENCE_MUST_BE_OUTSIDE_CHECKOUT')
    out.mkdir(parents=True, exist_ok=False)
    require(git(root,'rev-parse','HEAD')==a.expected_parent, 'SOURCE_PARENT_MISMATCH')
    require(not git(root,'status','--porcelain','--untracked-files=all'), 'SOURCE_NOT_CLEAN')
    before=(root/SOURCE).read_bytes(); require(blob(before)==SOURCE_BLOB, 'ORIGINAL_PRODUCER_BLOB_CHANGED')
    require(before.count(LINE.encode())==1 and b"stage_cfg['files']" not in before, 'PATCH_CONTEXT_CHANGED')
    require(not (root/TEST).exists() and not (root/HISTORY).exists(), 'CANDIDATE_ALREADY_EXISTS')
    if a.publish_review_branch:
        require(request('GET','/git/ref/heads/'+BRANCH)['object']['sha']==a.expected_parent, 'REVIEW_BRANCH_MOVED')
        require(request('GET','/git/ref/heads/main')['object']['sha']==MAIN, 'MAIN_MOVED_REINSPECT')
    template=Path(__file__).with_name('test_capture_coverage.py').read_bytes()
    (root/TEST).write_bytes(template)
    check_tests(root, out/'ORIGINAL_FOCUSED_TESTS.json', False)
    after=before.replace(LINE.encode(),(LINE+ADDITION).encode())
    (root/SOURCE).write_bytes(after)
    check_tests(root, out/'CANDIDATE_FOCUSED_TESTS.json', True)
    old_sha,new_sha=sha(before),sha(after)
    history=root/HISTORY; history.mkdir(parents=True)
    (history/'original-real_paint.py.txt').write_bytes(before)
    changed=[SOURCE,TEST,HISTORY+'/original-real_paint.py.txt']
    ledgers=[]
    path='manifests/post_dir_integration_004.json'
    raw=(root/path).read_bytes(); original=json.loads(raw); updated=copy.deepcopy(original)
    rows=[r for r in updated['source_members'] if r['canonical_path']==SOURCE]
    require(bool(rows), 'ACTIVE_SOURCE_LEDGER_ENTRY_MISSING')
    for row in rows:
        require(row['canonical_sha256']==old_sha, 'ACTIVE_SOURCE_LEDGER_HASH_MISMATCH')
        row['canonical_sha256']=new_sha
    require(len(updated['source_members'])==len(original['source_members']), 'SOURCE_MEMBER_COUNT_CHANGED')
    pattern=rb'("canonical_sha256"\s*:\s*")'+old_sha.encode()+rb'(")'
    anchors=list(re.finditer(rb'^  "source_members": \[',raw,re.MULTILINE))
    require(len(anchors)==1, 'SOURCE_MEMBERS_SECTION_AMBIGUOUS')
    start=anchors[0].start()
    tail,count=re.subn(pattern,lambda m:m.group(1)+new_sha.encode()+m.group(2),raw[start:])
    data=raw[:start]+tail
    require(count==len(rows) and json.loads(data)==updated, 'ONLY_CANONICAL_HASH_EDIT_REQUIRED')
    (root/path).write_bytes(data)
    snapshot=HISTORY+'/original-post_dir_integration_004.json'
    (root/snapshot).write_bytes(raw); changed += [path,snapshot]
    ledgers.append({'path':path,'before_sha256':sha(raw),'after_sha256':sha(data),
                    'canonical_hash_rows_updated':len(rows),'preserved_before_image':snapshot,
                    'only_semantic_change':'canonical_sha256 for '+SOURCE})
    path='manifests/lossless_migration.csv'; raw=(root/path).read_bytes()
    reader=csv.DictReader(io.StringIO(raw.decode())); fields=reader.fieldnames; records=list(reader)
    rows=[r for r in records if r['canonical_path']==SOURCE]
    if rows:
        for row in rows:
            require(row['canonical_sha256']==old_sha, 'LOSSLESS_LEDGER_HASH_MISMATCH')
            row['canonical_sha256']=new_sha
        stream=io.StringIO(newline=''); writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
        writer.writeheader(); writer.writerows(records); data=stream.getvalue().encode()
        snapshot=HISTORY+'/original-lossless_migration.csv'
        (root/snapshot).write_bytes(raw); (root/path).write_bytes(data); changed += [path,snapshot]
        ledgers.append({'path':path,'before_sha256':sha(raw),'after_sha256':sha(data),
                       'canonical_hash_rows_updated':len(rows),'preserved_before_image':snapshot,
                       'only_semantic_change':'canonical_sha256 for '+SOURCE})
    receipt={'schema_version':'bie.r04.capture-source-adaptation.v1','parent_commit':a.expected_parent,
             'historical_main':MAIN,'path':SOURCE,'before_git_blob':blob(before),'after_git_blob':blob(after),
             'before_sha256':old_sha,'after_sha256':new_sha,
             'reason':'Include executable QA helper explicitly; reproduced actual TypeScript coverage omission',
             'ledgers':ledgers,'source_delta':ADDITION,'new_test_file':TEST,
             'pre_patch_focused_result':{'tests':8,'failures':1,'errors':1,'skips':0},
             'post_patch_focused_result':{'tests':8,'failures':0,'errors':0,'skips':0},
             'real_compile_render':'NOT_RUN_AT_SOURCE_COMMIT','product_accepted':False,
             'historical_results_changed':False,'source_coverage_gate_changed':False,
             'canonical_verifiers_changed':False,'dependency_pins_changed':False}
    save(history/'SOURCE_ADAPTATION.json',receipt); changed.append(HISTORY+'/SOURCE_ADAPTATION.json')
    for name,args in [('assembly',['scripts/verify_assembly.py']),
                      ('canonical',['scripts/audit_canonical.py','--output',str(out/'CANONICAL_PRESERVATION.json')]),
                      ('post-dir',['scripts/verify_post_dir.py','--output',str(out/'POST_DIR_PRESERVATION.json')])]:
        r=subprocess.run([sys.executable,'-B',*args],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=300)
        (out/(name+'.log')).write_text(r.stdout)
        require(r.returncode==0, 'UNCHANGED_PRESERVATION_GATE_FAILED:'+name)
    git(root,'add','--',*changed)
    staged=git(root,'diff','--cached','--name-only').splitlines()
    require(set(staged)==set(changed), 'UNEXPECTED_STAGED_PATH')
    (out/'SOURCE_CANDIDATE.patch').write_text(git(root,'diff','--cached','--binary')+'\n')
    local_tree=git(root,'write-tree')
    result={'source_tree':local_tree,'parent_commit':a.expected_parent,'changed_files':changed,
            'published':False,'accepted':False,'render_verified':False}
    if a.publish_review_branch:
        require(request('GET','/git/ref/heads/'+BRANCH)['object']['sha']==a.expected_parent,'REVIEW_BRANCH_MOVED_BEFORE_PUBLISH')
        # Git's pack/delta transport avoids resending the large adoption ledger
        # through a JSON blob API. Existing exact before-image blobs are reused.
        token=os.environ.get('GH_TOKEN'); require(bool(token),'EXPLICIT_GITHUB_TOKEN_REQUIRED')
        env=dict(os.environ, GIT_AUTHOR_NAME='BIE R04 validation',
                 GIT_AUTHOR_EMAIL='noreply@users.noreply.github.com',
                 GIT_COMMITTER_NAME='BIE R04 validation',
                 GIT_COMMITTER_EMAIL='noreply@users.noreply.github.com')
        message=('fix(comp): retain executable capture helper in pinned TypeScript program\n\n'
                 'R04 reproduced coverage defect only. Eight focused tests; original source '
                 'and adoption ledgers preserved; active canonical hashes traceably updated. '
                 'No guard weakening, dependency downgrade, main merge, or acceptance promotion.\n')
        source_sha=subprocess.check_output(['git','commit-tree',local_tree,'-p',a.expected_parent],
                 cwd=root,env=env,input=message,text=True).strip()
        require(re.fullmatch('[0-9a-f]{40}',source_sha) is not None,'INVALID_SOURCE_COMMIT')
        auth=base64.b64encode(('x-access-token:'+token).encode()).decode()
        env.update(GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
                   GIT_CONFIG_VALUE_0='AUTHORIZATION: basic '+auth,
                   GIT_CONFIG_KEY_1='credential.helper',GIT_CONFIG_VALUE_1='',GIT_TERMINAL_PROMPT='0')
        process=subprocess.run(['git','push','https://github.com/'+REPO+'.git',
                                source_sha+':refs/heads/'+BRANCH],cwd=root,env=env,
                               capture_output=True,text=True,timeout=180,check=False)
        log=(process.stdout+process.stderr).replace(token,'[REDACTED]').replace(auth,'[REDACTED]')
        (out/'git-publication.log').write_text(log)
        require(process.returncode==0,'NONFORCED_REVIEW_BRANCH_PUBLICATION_FAILED')
        require(request('GET','/git/ref/heads/'+BRANCH)['object']['sha']==source_sha,'REMOTE_REF_READBACK_MISMATCH')
        remote=request('GET','/git/commits/'+source_sha)
        require(remote['tree']['sha']==local_tree,'REMOTE_TREE_MISMATCH')
        require(request('GET','/git/ref/heads/main')['object']['sha']==MAIN,'MAIN_CHANGED_EXTERNALLY')
        result.update(source_sha=source_sha,published=True,branch=BRANCH)
        output=os.environ.get('GITHUB_OUTPUT')
        if output:
            with open(output,'a') as f: f.write('source_sha='+source_sha+'\nsource_tree='+local_tree+'\n')
    save(out/'SOURCE_PUBLICATION.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
