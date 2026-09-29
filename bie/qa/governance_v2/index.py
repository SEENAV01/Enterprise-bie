"""HARD005 normalizes local task/code/spec/suite and adoption metadata.

An index is a checked map, not task acceptance or a replacement for historical files.
Blueprints and receipt references are operator inputs. Regeneration reads actual bytes;
verification compares the complete index, never a subset supplied by the index itself.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path,PurePosixPath
import ast,hashlib,os,stat,json
from ..release_v2.contracts import ContractError,canonical_bytes,digest,token

SCHEMA='bie.qa.task-integration-index/1'
MAX_FILE=32*1024*1024

def safe_file(root,path):
    if type(path)is not str or not path or '\\' in path or ':' in path or '\x00' in path:raise ContractError('INDEX_PATH')
    q=PurePosixPath(path)
    if q.is_absolute() or '..' in q.parts or str(q)!=path:raise ContractError('INDEX_PATH')
    root=Path(root)
    if root.is_symlink() or not root.is_dir():raise ContractError('INDEX_ROOT')
    parent=root
    for piece in q.parts:
        parent=parent/piece
        try:mode=parent.lstat().st_mode
        except OSError as exc:raise ContractError('INDEX_MISSING_FILE',path) from exc
        if stat.S_ISLNK(mode):raise ContractError('INDEX_SYMLINK',path)
    if not stat.S_ISREG(mode):raise ContractError('INDEX_NOT_REGULAR',path)
    return parent

def read_file(root,path):
    p=safe_file(root,path)
    # Read-only local workspace checker, not a hostile concurrent filesystem sandbox.
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as f:
        before=os.fstat(f.fileno())
        if before.st_size>MAX_FILE:raise ContractError('INDEX_FILE_LIMIT')
        data=f.read(MAX_FILE+1);after=os.fstat(f.fileno())
    if len(data)>MAX_FILE or (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):raise ContractError('INDEX_FILE_CHANGED')
    return data

def reference(root,path):
    data=read_file(root,path)
    return dict(path=path,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))

def load(root,path):
    from ..publication_v2.contracts import strict_json
    return strict_json(read_file(root,path))


def symbol_reference(root,path,symbol):
    ref=reference(root,path)
    try:tree=ast.parse(read_file(root,path).decode('utf-8'))
    except (SyntaxError,UnicodeError,RecursionError) as exc:raise ContractError('INDEX_SOURCE_PARSE') from exc
    matches=[]
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and node.name==symbol:matches.append(node)
        if isinstance(node,ast.ClassDef):
            for child in node.body:
                if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name+'.'+child.name==symbol:matches.append(child)
    if len(matches)!=1:raise ContractError('INDEX_SYMBOL_NOT_UNIQUE',symbol)
    node=matches[0];return dict(**ref,symbol=symbol,start_line=node.lineno,end_line=node.end_lineno)


def test_index(root,receipt_path,suite_specs):
    """Require exact case inventories and current source/test hashes in actual receipt."""
    receipt=load(root,receipt_path)
    if receipt.get('passed') is not True or receipt.get('full_repository_regression')is not False:raise ContractError('INDEX_RECEIPT_NOT_LOCAL_PASS')
    for field in ('code_hashes','test_hashes'):
        hashes=receipt.get(field)
        if type(hashes)is not dict or not hashes:raise ContractError('INDEX_RECEIPT_HASHES')
        for path,value in hashes.items():
            if reference(root,path)['sha256']!=value:raise ContractError('INDEX_STALE_TEST_RECEIPT',path)
    expected={x[0]:(x[1],x[2]) for x in suite_specs}
    suites=receipt.get('suites',[])
    if type(suites)is not list or len(suites)!=len(expected):raise ContractError('INDEX_SUITE_CENSUS')
    rows=[];seen=set();summaries=[]
    for suite in suites:
        name=suite['suite']
        if name in seen or name not in expected:raise ContractError('INDEX_DUPLICATE_SUITE')
        seen.add(name);directory,count=expected[name]
        if suite.get('path')!=directory or suite.get('run')!=count or suite.get('success')is not True or any(suite.get(x)!=0 for x in ('failures','errors','skipped')):raise ContractError('INDEX_SUITE_RESULT')
        ids=suite.get('test_ids',[])
        if type(ids)is not list or len(ids)!=count or len(set(ids))!=count:raise ContractError('INDEX_TEST_CENSUS')
        summaries.append(dict(suite_id=name,test_directory=directory,unique_tests=count,status='EXECUTED_PASS'))
        for ident in ids:
            if type(ident)is not str or len(ident.split('.'))<3:raise ContractError('INDEX_TEST_ID')
            module=ident.split('.')[0];token(module,'test.module')
            path=directory+'/'+module+'.py';ref=reference(root,path)
            if receipt['test_hashes'].get(path)!=ref['sha256']:raise ContractError('INDEX_TEST_SOURCE_PROVENANCE',path)
            rows.append(dict(suite_id=name,test_id=ident,qualified_id=name+'::'+path+'::'+ident,source=ref))
    if len({x['qualified_id'] for x in rows})!=len(rows):raise ContractError('INDEX_TEST_ID_ALIAS')
    if len(rows)!=receipt.get('unique_suite_qualified_tests'):raise ContractError('INDEX_TEST_TOTAL')
    return dict(receipt=reference(root,receipt_path),suite_count=len(summaries),unique_tests=len(rows),
        suites=sorted(summaries,key=lambda x:x['suite_id']),tests=sorted(rows,key=lambda x:x['qualified_id']),full_repository_regression=False)


def build_index(root,blueprint,*,receipt_path,suite_specs):
    """Blueprint comes from checked operator registry; never recover it from submitted index."""
    from .catalog import ORIGINAL_TASK_IDS,HARDENING_TASK_IDS,ORIGINAL_TASK_MAP,ORIGINAL_NAMESPACES
    required={'schema_version','checkpoint','latest_task_ids','original_rows','namespaces','metadata_paths','hardening_state_path','hardening_evidence'}
    if type(blueprint)is not dict or set(blueprint)!=required or blueprint['schema_version']!='bie.qa.index-blueprint/1':raise ContractError('INDEX_BLUEPRINT')
    if type(blueprint['metadata_paths'])is not dict or set(blueprint['metadata_paths'])!={'continuation','result','integration_plan'}:raise ContractError('INDEX_METADATA_PATHS')
    original=blueprint['original_rows']
    if len(original)!=len(ORIGINAL_TASK_IDS) or {r['task_id'] for r in original}!=set(ORIGINAL_TASK_IDS):raise ContractError('INDEX_ORIGINAL_TASK_CENSUS')
    if any((row['original_capability'],row['source_namespace'])!=ORIGINAL_TASK_MAP[row['task_id']] for row in original):raise ContractError('INDEX_TASK_BASELINE_CHANGED')
    if not set(ORIGINAL_NAMESPACES)<=set(blueprint['namespaces']):raise ContractError('INDEX_BASELINE_NAMESPACE_MISSING')
    actual_namespaces={p.relative_to(Path(root)).as_posix() for p in (Path(root)/'bie/qa').iterdir() if p.is_dir() and p.name.endswith('_v2')}
    if actual_namespaces!=set(blueprint['namespaces']):raise ContractError('INDEX_NAMESPACE_CENSUS')
    tests=test_index(root,receipt_path,suite_specs);by_suite={s['suite_id']:s for s in tests['suites']}
    namespaces=[]
    for ns in sorted(actual_namespaces):
        code=[reference(root,p.relative_to(root).as_posix()) for p in sorted((Path(root)/ns).rglob('*.py'))]
        if not code:raise ContractError('INDEX_EMPTY_NAMESPACE')
        namespaces.append(dict(namespace=ns,source_files=code,canonical_adoption='NOT_VERIFIED',strategy='LATEST_HEAD_COMPARE_AND_REVIEWED_RECONCILIATION'))
    tasks=[]
    for row in original:
        suite=row['shared_suite_name']
        if suite not in by_suite or by_suite[suite]['test_directory']!=row['test_directory']:raise ContractError('INDEX_TASK_SUITE_MAPPING')
        paths=row['task_evidence_paths']
        if not paths:raise ContractError('INDEX_TASK_EVIDENCE_MISSING')
        tasks.append(dict(task_id=row['task_id'],capability=row['original_capability'],namespace=row['source_namespace'],
            entrypoint=symbol_reference(root,row['entrypoint']['path'],row['entrypoint']['symbol']),
            specification=reference(root,row['spec']['path']),historical_task_evidence=[reference(root,p) for p in sorted(paths)],
            suite_id=suite,independent_task_test_count=None,implementation='BOUNDED_LOCAL',integration='NOT_VERIFIED',product_accepted=False))
    state=load(root,blueprint['hardening_state_path']);entries=state.get('tasks',[])
    if len(entries)!=len(HARDENING_TASK_IDS) or {e['task_id'] for e in entries}!=set(HARDENING_TASK_IDS):raise ContractError('INDEX_HARDENING_CENSUS')
    implemented={e['task_id'] for e in entries if e['status']=='IMPLEMENTED_LOCAL_VERIFIED_PENDING_SECTION_REAUDIT'}
    for e in entries:
        if e['status'] not in ('PLANNED_NOT_IMPLEMENTED','IMPLEMENTED_LOCAL_VERIFIED_PENDING_SECTION_REAUDIT'):raise ContractError('INDEX_UNSUPPORTED_TASK_STATUS')
        if e['task_id'] in implemented and not set(e['dependencies'])<=implemented:raise ContractError('INDEX_UNMET_LOCAL_DEPENDENCY')
    if not set(blueprint['latest_task_ids'])<=implemented:raise ContractError('INDEX_LATEST_NOT_IMPLEMENTED')
    hard_refs=blueprint['hardening_evidence']
    if type(hard_refs)is not dict or set(hard_refs)!=implemented:raise ContractError('INDEX_HARDENING_EVIDENCE_CENSUS')
    hard_rows=[]
    for e in entries:
        value=dict(task_id=e['task_id'],status=e['status'],dependencies=e['dependencies'])
        if e['task_id']in implemented:
            h=hard_refs[e['task_id']]
            if set(h)!={'source_paths','specification','task_evidence','suite_id'} or not h['source_paths'] or not h['task_evidence'] or h['suite_id']not in by_suite:raise ContractError('INDEX_HARDENING_EVIDENCE')
            value.update(source_files=[reference(root,p) for p in h['source_paths']],specification=reference(root,h['specification']),
                historical_task_evidence=[reference(root,p) for p in h['task_evidence']],suite_id=h['suite_id'],independent_task_test_count=None)
        hard_rows.append(value)
    cont=load(root,blueprint['metadata_paths']['continuation']);result=load(root,blueprint['metadata_paths']['result'])
    plan=load(root,blueprint['metadata_paths']['integration_plan'])
    latest=blueprint['latest_task_ids']
    if cont.get('latest_checkpoint')!=blueprint['checkpoint'] or cont.get('latest_task_ids')!=latest or cont.get('hardening_tasks_with_local_implementation')!=len(implemented):raise ContractError('INDEX_STALE_CONTINUATION')
    if result.get('task_ids')!=latest or result.get('batch_id')!=cont.get('batch_id'):raise ContractError('INDEX_STALE_RESULT')
    if plan.get('latest_checkpoint')!=blueprint['checkpoint'] or set(plan.get('cumulative_source_namespaces',[]))!=actual_namespaces:raise ContractError('INDEX_STALE_INTEGRATION_PLAN')
    if {r.get('namespace') for r in plan.get('namespace_actions',[])}!=actual_namespaces:raise ContractError('INDEX_INTEGRATION_ACTION_CENSUS')
    if plan.get('execute_automatically')is not False or plan.get('all_preconditions_satisfied')is not False:raise ContractError('INDEX_UNSUPPORTED_INTEGRATION_CLAIM')
    for flag in ('github_integrated','product_accepted','full_section_complete'):
        if cont.get(flag)is not False:raise ContractError('INDEX_UNSUPPORTED_ACCEPTANCE_CLAIM')
    return dict(schema_version=SCHEMA,checkpoint=blueprint['checkpoint'],latest_task_ids=latest,blueprint_digest=digest(blueprint),
        original_tasks=sorted(tasks,key=lambda x:x['task_id']),hardening_state=reference(root,blueprint['hardening_state_path']),
        hardening_tasks=hard_rows,
        namespaces=namespaces,tests=tests,metadata={k:reference(root,v) for k,v in blueprint['metadata_paths'].items()},
        historical_evidence_is_not_current_acceptance=True,github_integrated=False,section15_modified=False,product_accepted=False)


def verify_index(root,submitted,blueprint,*,receipt_path,suite_specs):
    expected=build_index(root,blueprint,receipt_path=receipt_path,suite_specs=suite_specs)
    if canonical_bytes(submitted)!=canonical_bytes(expected):raise ContractError('INDEX_CONTENT_MISMATCH')
    return dict(status='VERIFIED_LOCAL_INDEX',original_tasks=len(expected['original_tasks']),namespaces=len(expected['namespaces']),
        hardening_tasks=len(expected['hardening_tasks']),unique_tests=expected['tests']['unique_tests'],index_digest=digest(expected),product_accepted=False)
