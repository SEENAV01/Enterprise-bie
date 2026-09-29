"""HARD036: pinned Git checkout and suite-qualified unittest registry.

A supplied commit string or historic local test receipt is not a canonical run.
Registration discovers actual cases in isolated processes from the exact checked
revision. Execution requires the separately approved registration digest and
rechecks tracked/untracked files before and after all processes. Tests are trusted;
production worker isolation and non-unittest adapters remain separate obligations.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,os,subprocess,tempfile,signal,sys,time
from .common import *

@dataclass(frozen=True)
class Suite:
    suite_id:str
    directory:str
    def __post_init__(self):token(self.suite_id,'suite');safe_relative_path(self.directory)

@dataclass(frozen=True)
class CorpusPolicy:
    repository:str
    revision:str
    tree:str
    suites:tuple[Suite,...]
    evidence_kind:str='DIAGNOSTIC_REPOSITORY'
    timeout_seconds:int=60
    max_files:int=100000
    def __post_init__(self):
        text(self.repository,'repository',300)
        from ..release_v2.contracts import revision
        revision(self.revision);revision(self.tree)
        require(type(self.suites) is tuple and 1<=len(self.suites)<=256 and all(type(s) is Suite for s in self.suites),'H6_CORPUS_SUITES')
        require(len({s.suite_id for s in self.suites})==len(self.suites),'H6_CORPUS_SUITE_ALIAS')
        require(self.evidence_kind in ('DIAGNOSTIC_REPOSITORY','CANONICAL_CHECKOUT'),'H6_CORPUS_KIND')
        integer(self.timeout_seconds,'timeout',1,600);integer(self.max_files,'max files',1,100000)
    @property
    def content_digest(self):return digest(asdict(self))

def _git(root,args):
    env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_TERMINAL_PROMPT':'0','LANG':'C.UTF-8'}
    r=subprocess.run(['git','-C',str(root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,env=env)
    require(r.returncode==0,'H6_CHECKOUT_GIT_FAILED')
    require(len(r.stdout)<=32*1024*1024,'H6_GIT_OUTPUT_LIMIT');return r.stdout

def verify_checkout(root,policy):
    root=Path(root)
    require(type(policy) is CorpusPolicy and root.is_dir() and not root.is_symlink(),'H6_CHECKOUT_ROOT')
    require((root/'.git').exists() and not (root/'.git').is_symlink(),'H6_CHECKOUT_GIT_REQUIRED')
    require(_git(root,['rev-parse','HEAD']).decode().strip()==policy.revision,'H6_CHECKOUT_REVISION')
    require(_git(root,['rev-parse','HEAD^{tree}']).decode().strip()==policy.tree,'H6_CHECKOUT_TREE')
    # No diff/smudge filters or hooks execute: object IDs are compared from raw bytes.
    raw=_git(root,['ls-tree','-rz','--full-tree','HEAD']);entries=[]
    for row in raw.split(b'\0'):
        if not row:continue
        meta,name=row.split(b'\t',1);mode,kind,oid=meta.decode().split();path=name.decode('utf-8')
        safe_relative_path(path);require(kind=='blob' and mode in ('100644','100755'),'H6_CHECKOUT_UNSUPPORTED_ENTRY')
        p=root/path
        for parent in (p,)+tuple(p.parents):
            if parent==root.parent:break
            require(not parent.is_symlink(),'H6_CHECKOUT_SYMLINK')
        require(p.is_file() and p.stat().st_size<=64*1024*1024,'H6_CHECKOUT_FILE_BUDGET')
        value=p.read_bytes();gitsha=hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()
        require(gitsha==oid,'H6_CHECKOUT_DIRTY_FILE')
        entries.append(dict(path=path,git_blob=oid,sha256=hashlib.sha256(value).hexdigest(),bytes=len(value)))
        require(len(entries)<=policy.max_files,'H6_CHECKOUT_FILE_COUNT')
    # Include ignored files too: test/fixture shadows and stale bytecode must not load.
    extras=_git(root,['ls-files','--others','-z']).split(b'\0')
    require(not any(extras),'H6_CHECKOUT_UNTRACKED_FILES')
    paths={e['path'] for e in entries};test_paths={p for p in paths if Path(p).name.startswith('test_') and p.endswith('.py')}
    require(bool(test_paths),'H6_CHECKOUT_NO_TESTS')
    for path in test_paths:
        coverage=[s for s in policy.suites if path.startswith(s.directory+'/')]
        require(len(coverage)==1,'H6_CORPUS_TEST_SOURCE_CENSUS')
    return dict(repository=policy.repository,revision=policy.revision,tree=policy.tree,files=sorted(entries,key=lambda r:r['path']),
        test_sources=sorted(test_paths),evidence_kind=policy.evidence_kind)

def _suite(root,suite,policy,execute):
    worker=Path(__file__).with_name('case_worker.py');identity=hashlib.sha256(worker.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='bie-h6-corpus-') as d:
        output=Path(d)/'result.json';log=Path(d)/'log.txt'
        cmd=[sys.executable,'-I','-B',str(worker),'--root',str(Path(root).resolve()),'--directory',suite.directory,'--output',str(output)]
        if execute:cmd.append('--run')
        start=time.monotonic();timed=False
        with log.open('wb') as f:
            p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,
                env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'PYTHONDONTWRITEBYTECODE':'1','LANG':'C.UTF-8'})
            try:code=p.wait(policy.timeout_seconds)
            except subprocess.TimeoutExpired:timed=True;code=None
            finally:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                p.wait(timeout=3)
        require(not timed,'H6_CORPUS_TIMEOUT')
        require(output.is_file() and output.stat().st_size<=16*1024*1024,'H6_CORPUS_NO_RECEIPT')
        result=strict_json(output.read_bytes());require(type(result) is dict,'H6_CORPUS_WORKER_PROTOCOL')
        require(result['executed'] is execute,'H6_CORPUS_EXECUTION_KIND')
        if not execute:require(code==0,'H6_CORPUS_DISCOVERY_FAILED')
        result.update(suite_id=suite.suite_id,directory=suite.directory,process_exit=code,worker_sha256=identity,
                      elapsed_ms=int((time.monotonic()-start)*1000),log=log.read_text(errors='replace')[-1_000_000:])
        return result

def register(root,policy):
    before=verify_checkout(root,policy);rows=[]
    for s in policy.suites:
        row=_suite(root,s,policy,False)
        for c in row['cases']:
            require(c['source'] in {f['path'] for f in before['files']},'H6_CORPUS_FOREIGN_TEST_SOURCE')
        rows.append(row)
    require(verify_checkout(root,policy)==before,'H6_CORPUS_DISCOVERY_MUTATED_CHECKOUT')
    cases=[dict(suite_id=r['suite_id'],qualified_id=r['suite_id']+'::'+c['test_id'],**c) for r in rows for c in r['cases']]
    require(len({c['qualified_id'] for c in cases})==len(cases),'H6_CORPUS_CASE_ALIAS')
    result=dict(schema_version='bie.qa.checkout-corpus/1',policy_digest=policy.content_digest,checkout=before,cases=cases,
                full_repository_tests_executed=False,registration_requires_independent_approval=True)
    result['content_digest']=digest(result);return result

def execute_registered(root,policy,registration,*,approved_digest):
    expected=dict(registration);stored=expected.pop('content_digest',None)
    require(stored==digest(expected)==approved_digest,'H6_CORPUS_APPROVAL_DIGEST')
    require(registration['policy_digest']==policy.content_digest,'H6_CORPUS_POLICY_CHANGED')
    checkout=verify_checkout(root,policy);require(checkout==registration['checkout'],'H6_CORPUS_CHECKOUT_CHANGED')
    rows=[_suite(root,s,policy,True) for s in policy.suites]
    actual=[dict(suite_id=r['suite_id'],qualified_id=r['suite_id']+'::'+c['test_id'],**c) for r in rows for c in r['cases']]
    require(actual==registration['cases'],'H6_CORPUS_EXECUTED_CASE_CENSUS')
    for r in rows:
        require(r['run']==len(r['cases']) and sorted(r['executed_ids'])==sorted(c['test_id'] for c in r['cases']),'H6_CORPUS_MISSING_EXECUTION')
    require(verify_checkout(root,policy)==checkout,'H6_CORPUS_TEST_MUTATED_CHECKOUT')
    return dict(schema_version='bie.qa.checkout-corpus-run/1',registration_digest=approved_digest,policy_digest=policy.content_digest,
        runs=rows,unique_tests=len(actual),all_passed=all(r['passed'] and r['process_exit']==0 for r in rows),
        full_canonical_regression=policy.evidence_kind=='CANONICAL_CHECKOUT',
        native_repository=policy.repository,evidence_kind=policy.evidence_kind,product_accepted=False)
