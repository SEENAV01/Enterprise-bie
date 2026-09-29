"""SEC001/002: exact source scope, non-executing scans and boundary evidence QA.

Static findings and fixed diagnostic probes cannot certify hostile code execution.
No submitted program is executed by this evaluator.
"""
from dataclasses import dataclass
from pathlib import Path,PurePosixPath
import errno,hashlib
from ..release_v2.contracts import ContractError,canonical_bytes,digest,integer,sha256
from ..source_v2.models import Report,Finding
from ..source_v2.io import SnapshotStore
from ..source_v2.codec import loads
from ..repair_v2.models import Snapshot
from ..repair_v2.planner import approved
from ..repair_audit_v2.io import verify_files,fields,equal
from ..reasoning_v2.attestation import Review,ReviewVerifier
from .models import SecurityRequest,SecurityPolicy,PROBES,CONTROLS
from .scanner import scan,Toolchain

LIMITATIONS=(
 'Static parsing does not prove unrestricted generated code is safe; no taint/supply-chain vulnerability database scan or whole-program proof.',
 'Restricted PURE/DATA profiles are deliberately narrower than real React/Remotion/game applications.',
 'Dependency bytes/versions and exact scripts are inspected; transitive dependency closure, upstream ownership and current vulnerabilities need independent checks.',
 'The included sandbox launcher runs only bundled benign probes, not candidate code or kernel exploits.',
 'Linux x86_64 chroot plus UID/capability drop and seccomp tests cover declared operations, not kernel/runtime vulnerabilities, side channels or resource aggregate isolation.',
 'No browser/Node/native BIE producer sandbox, network namespace/cgroup integration, complete security certification or product acceptance is established.'
)
@dataclass(frozen=True,slots=True)
class Result:
    reports:tuple[Report,...]
    details_json:str
    @property
    def status(self):
        states={r.status for r in self.reports}
        return 'BLOCKED' if 'BLOCKED' in states else 'REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in states else 'CHECKS_PASSED'
    def to_dict(self):return dict(schema_version='bie.qa.security-result/1',reports=[r.to_dict() for r in self.reports],details=loads(self.details_json.encode()),status=self.status,product_accepted=False,hostile_code_execution_certified=False)

def review_targets(request,policy):
    all_ids=tuple(sorted(a.artifact_id for a in request.snapshot.artifacts))
    targets={('inventory','security-inventory'):all_ids,('support','security-code'):tuple(sorted(u.artifact_id for u in policy.units))}
    if policy.dependencies:targets['support','security-dependencies']=tuple(sorted(d.artifact_id for d in policy.dependencies))
    if request.sandbox_evidence:targets['support','security-boundaries']=(request.sandbox_evidence.artifact_id,)
    return targets

def inspect_sandbox(raw,snapshot_digest,now,max_age):
    fields(raw,{'schema_version','execution_id','snapshot_digest','started_at','finished_at','worker_sha256','interpreter_sha256','profile','platform','processes','observations','outside_canary_unchanged','status','candidate_executed','product_accepted'},'SEC_SANDBOX_FIELDS')
    if raw['schema_version']!='bie.qa.sandbox-diagnostics/1' or raw['profile']!='LINUX_CHROOT_SECCOMP_FIXED_PROBES_V1':raise ContractError('SEC_SANDBOX_PROFILE')
    if raw['snapshot_digest']!=snapshot_digest:raise ContractError('SEC_SANDBOX_SNAPSHOT')
    if raw['product_accepted'] is not False or raw['candidate_executed'] is not False:raise ContractError('SEC_SANDBOX_OVERCLAIM')
    if type(raw['execution_id']) is not str or not raw['execution_id'].startswith('sec-') or len(raw['execution_id'])>128:raise ContractError('SEC_EXECUTION_ID')
    for n in ('started_at','finished_at'):integer(raw[n],n)
    if not 0<=raw['finished_at']-raw['started_at']<=60 or not 0<=now-raw['started_at']<=max_age or raw['finished_at']>now:raise ContractError('SEC_SANDBOX_TIME')
    sha256(raw['interpreter_sha256'],'interpreter_sha256')
    expected_worker=hashlib.sha256(Path(__file__).with_name('boundary_worker.py').read_bytes()).hexdigest()
    if raw['worker_sha256']!=expected_worker:raise ContractError('SEC_PROBE_WORKER_IDENTITY')
    if raw['outside_canary_unchanged'] is not True:raise ContractError('SEC_OUTSIDE_CANARY_CHANGED')
    if raw['status']!='CHECKS_PASSED':raise ContractError('SEC_BOUNDARY_NOT_PASSED')
    processes=raw['processes']
    if type(processes) is not list or len(processes)!=3:raise ContractError('SEC_PROCESS_COVERAGE')
    cases=set();nonces=set();seen_ids=set();combined=[]
    for p in processes:
        fields(p,{'case','execution_id','exit_code','elapsed_ms','stdout_sha256','stderr_sha256','stdout','stderr','receipt'},'SEC_PROCESS_FIELDS')
        case=p['case']
        if case not in ('standard','file_limit','descriptor_limit') or case in cases:raise ContractError('SEC_PROCESS_CASE')
        cases.add(case)
        if p['execution_id']!=raw['execution_id']+'-'+case or p['execution_id'] in seen_ids:raise ContractError('SEC_REPLAYED_PROCESS')
        seen_ids.add(p['execution_id'])
        if type(p['exit_code']) is not int or p['exit_code']!=0:raise ContractError('SEC_PROBE_EXIT')
        integer(p['elapsed_ms'],'elapsed_ms',0,15000)
        for k in ('stdout','stderr'):
            if type(p[k]) is not str or len(p[k].encode())>65536 or hashlib.sha256(p[k].encode()).hexdigest()!=p[k+'_sha256']:raise ContractError('SEC_PROBE_LOG_IDENTITY')
        if p['stderr']:raise ContractError('SEC_PROBE_STDERR')
        child=loads(p['stdout'].encode());equal(child,p['receipt'],'SEC_CHILD_LOG_MISMATCH')
        fields(child,{'schema_version','case','nonce','code_executed','profile','controls','observations','status'},'SEC_CHILD_FIELDS')
        if child['schema_version']!='bie.qa.boundary-child/1' or child['case']!=case or child['profile']!=raw['profile'] or child['code_executed'] is not False or child['status']!='CHECKS_PASSED':raise ContractError('SEC_CHILD_SCOPE')
        if type(child['nonce']) is not str or len(child['nonce'])!=32 or any(c not in '0123456789abcdef' for c in child['nonce']) or child['nonce'] in nonces:raise ContractError('SEC_NONCE_REPLAY')
        nonces.add(child['nonce'])
        fields(child['controls'],set(CONTROLS),'SEC_CONTROL_COVERAGE')
        if any(v is not True for v in child['controls'].values()):raise ContractError('SEC_CONTROL_NOT_ENFORCED')
        rows=child['observations'];required=set(PROBES)-{'file_limit','descriptor_limit'} if case=='standard' else {case}
        if type(rows) is not list or len(rows)!=len(required):raise ContractError('SEC_PROBE_COVERAGE')
        probes=set()
        for x in rows:
            fields(x,{'probe','expected','observed','errno','passed'},'SEC_PROBE_FIELDS')
            name=x['probe']
            if name not in required or name in probes:raise ContractError('SEC_PROBE_DUPLICATE_OR_UNKNOWN')
            probes.add(name);integer(x['errno'],'errno',0,4096)
            if name in ('allowed_read','allowed_write'):expected=('ALLOW','ALLOWED');errors={0}
            elif name=='environment':expected=('ABSENT','ABSENT');errors={0}
            else:
                expected=('DENY','DENIED');errors={errno.EPERM,errno.EACCES}
                if name in ('outside_read','parent_traversal','symlink_read'):errors|={errno.ENOENT}
                if name=='inherited_fd':errors={errno.EBADF}
                if name=='file_limit':errors={errno.EFBIG}
                if name=='descriptor_limit':errors={errno.EMFILE}
                if name in ('ipv4_socket','ipv6_socket','unix_socket','spawn','exec','namespace','ptrace'):errors={errno.EPERM}
            if (x['expected'],x['observed'])!=expected or x['errno'] not in errors or x['passed'] is not True:raise ContractError('SEC_BOUNDARY_PROBE_FAILED')
        combined.extend(rows)
    equal(raw['observations'],combined,'SEC_PROBE_AGGREGATE_MISMATCH')
    return dict(verified_probe_count=len(combined),fixed_probe_processes=3,candidate_code_executed=False)

def evaluate(request,root,policy,*,as_of,reviews=(),verifier=None,toolchain=None):
    if type(request) is not SecurityRequest or type(policy) is not SecurityPolicy:raise ContractError('SEC_INPUT_TYPE')
    integer(as_of,'as_of');verifier=ReviewVerifier() if verifier is None else verifier
    if type(verifier) is not ReviewVerifier:raise ContractError('SEC_VERIFIER_TYPE')
    if type(reviews) is not tuple or len(reviews)>128 or any(type(x) is not Review for x in reviews) or len({x.review_id for x in reviews})!=len(reviews):raise ContractError('SEC_REVIEWS_TYPE')
    fs=[[],[]];inspected=set();details={'units':[],'authorization':{},'sandbox':None}
    def add(index,code,subject='security',severity='BLOCKER'):
        f=Finding(code,severity,subject,'SEC','Security requirement: '+code)
        if f not in fs[index]:fs[index].append(f)
    def auth(purpose,subject,ids,indices):
        relevant=tuple(r for r in reviews if (r.purpose,r.subject_id)==(purpose,subject))
        ok,codes=approved(relevant,verifier,subject=subject,purpose=purpose,request_digest=request.content_digest,policy=policy,evidence_ids=ids,now=as_of)
        details['authorization'][subject]=dict(verified=ok,codes=codes)
        if not ok:
            for idx in indices:add(idx,'SEC_AUTHORIZATION_REQUIRED',subject,'REVIEW')
            for r in relevant:
                a=verifier.verify_bound(r,request.content_digest,policy.content_digest,policy.max_receipt_age_seconds,as_of)
                if a.operational and r.verdict=='REJECTED':
                    for idx in indices:add(idx,'SEC_REVIEW_REJECTED',subject)
    try:
        if request.snapshot.content_digest!=policy.snapshot_digest:raise ContractError('SEC_SNAPSHOT_BINDING')
        full=Snapshot(request.snapshot.run_id,request.snapshot.revision,request.snapshot.artifacts+((request.sandbox_evidence,) if request.sandbox_evidence else ()))
        verify_files(root,full,exact=True)
        refs={a.artifact_id:a for a in request.snapshot.artifacts}
        with SnapshotStore(root) as store:blobs={a.artifact_id:store.read(a) for a in full.artifacts}
        inspected.update(blobs)
        targets=review_targets(request,policy)
        if any((r.purpose,r.subject_id) not in targets for r in reviews):raise ContractError('SEC_UNEXPECTED_REVIEW')
        for (purpose,subject),ids in targets.items():auth(purpose,subject,ids,range(2) if subject=='security-inventory' else (1,) if subject=='security-boundaries' else (0,))
        unit_ids={u.artifact_id for u in policy.units};dep_ids={d.artifact_id for d in policy.dependencies}
        if not unit_ids<=refs.keys() or not dep_ids<=refs.keys() or unit_ids&dep_ids:raise ContractError('SEC_SCOPE_IDENTITY')
        code_ext={'.py','.pyw','.ts','.tsx','.js','.jsx','.mjs','.cjs','.wasm','.sh','.ps1','.bat','.cmd','.so','.dll','.exe','.html','.htm','.svg','.xhtml','.css','.node','.pyd','.jar'}
        detected={a.artifact_id for a in refs.values() if PurePosixPath(a.path).suffix.lower() in code_ext or PurePosixPath(a.path).name=='package.json'}
        if detected-unit_ids:raise ContractError('SEC_EXECUTABLE_INVENTORY_GAP')
        if any(refs[i].role=='source' for i in unit_ids):add(0,'SEC_SOURCE_CODE_ROLE_REVIEW',severity='REVIEW')
        paths={a.path:a.artifact_id for a in refs.values()};deps={d.name for d in policy.dependencies}
        if toolchain is not None:
            if type(toolchain) is not Toolchain or (toolchain.node_sha256,toolchain.typescript_sha256)!=(policy.parser_node_sha256,policy.parser_typescript_sha256):raise ContractError('SEC_PARSER_POLICY_BINDING')
        for u in policy.units:
            try:
                allowed_ext={'PYTHON':{'.py','.pyw'},'TYPESCRIPT':{'.ts'},'TSX':{'.tsx'},'JAVASCRIPT':{'.js','.mjs','.cjs','.jsx'},'NPM_MANIFEST':{'.json'}}
                if PurePosixPath(refs[u.artifact_id].path).suffix.lower() not in allowed_ext[u.language]:raise ContractError('SEC_LANGUAGE_PATH_MISMATCH')
                results,imports,nodes=scan(blobs[u.artifact_id],u,policy,toolchain)
                for f in results:add(0,f['code'],u.artifact_id,f['severity'])
                details['units'].append(dict(artifact_id=u.artifact_id,nodes=nodes,findings=results,imports=imports))
                for module in imports:
                    if u.language=='PYTHON':continue # imports already cannot pass PURE; general imports need review
                    if module.startswith('.'):
                        base=PurePosixPath(refs[u.artifact_id].path).parent
                        # Resolve lexically; never follow a requested filesystem path.
                        parts=[]
                        for x in (base/module).parts:
                            if x=='..':
                                if not parts:raise ContractError('SEC_IMPORT_PATH_ESCAPE')
                                parts.pop()
                            elif x!='.':parts.append(x)
                        relative='/'.join(parts)
                        candidates=[relative,relative+'.ts',relative+'.tsx',relative+'.js',relative+'/index.ts',relative+'/index.js']
                        resolved=[paths[x] for x in candidates if x in paths]
                        if len(resolved)!=1 or resolved[0] not in unit_ids:add(0,'SEC_IMPORT_CLOSURE',u.artifact_id)
                    elif module not in deps:add(0,'SEC_UNAPPROVED_IMPORT',u.artifact_id)
                if u.language=='NPM_MANIFEST' and PurePosixPath(refs[u.artifact_id].path).name!='package.json':add(0,'SEC_MANIFEST_PATH',u.artifact_id)
            except (ContractError,RecursionError,MemoryError) as e:add(0,e.code if isinstance(e,ContractError) else 'SEC_PARSER_RESOURCE',u.artifact_id)
        if policy.dependencies:add(0,'SEC_TRANSITIVE_AND_VULNERABILITY_REVIEW',severity='REVIEW')
        if request.sandbox_evidence:
            try:details['sandbox']=inspect_sandbox(loads(blobs[request.sandbox_evidence.artifact_id]),request.snapshot.content_digest,as_of,policy.max_receipt_age_seconds)
            except (ContractError,TypeError,KeyError,ValueError) as e:add(1,e.code if isinstance(e,ContractError) else 'SEC_SANDBOX_MALFORMED')
        else:add(1,'SEC_SANDBOX_EVIDENCE_MISSING',severity='REVIEW')
        add(1,'SEC_NATIVE_GENERATED_RUNTIME_PENDING',severity='REVIEW')
        verify_files(root,full,exact=True)
    except (ContractError,OSError,UnicodeError) as exc:
        for i in range(2):add(i,exc.code if isinstance(exc,ContractError) else 'SEC_INPUT_IO')
    eid=digest(dict(request=request.content_digest,policy=policy.content_digest,verifier=verifier.configuration_digest,details=details))
    reports=tuple(Report(f'BIE-QA-SEC-{i+1:03}',request.content_digest,policy.content_digest,eid,as_of,
        tuple(sorted(fs[i],key=lambda f:(f.severity,f.code,f.subject_id))),
        (('code_units',len(policy.units)),('probe_observations',details['sandbox']['verified_probe_count'] if details['sandbox'] else 0)),
        tuple(sorted(inspected)),LIMITATIONS) for i in range(2))
    return Result(reports,canonical_bytes(details).decode())
