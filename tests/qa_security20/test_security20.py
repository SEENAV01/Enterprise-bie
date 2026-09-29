from pathlib import Path
from dataclasses import replace,asdict
import copy,hashlib,json,os,subprocess,sys,tempfile,unittest
from security20_support import *
from bie.qa.release_v2.contracts import ContractError,ReleaseCandidate,EvidenceBundle
from bie.qa.release_v2.evaluator import ReleaseEvaluator
from bie.qa.security_v2.scanner import scan_python,scan_typescript,scan_manifest
from bie.qa.security_v2.evaluator import inspect_sandbox
from bie.qa.security_v2.codec import decode
from bie.qa.source_v2.codec import loads

class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'snapshot';self.r,self.p,self.t=fixture(self.root)
    def check(self,code,r=None,p=None,**kw):
        result=run(r or self.r,self.root,p or self.p,**kw);self.assertIn(code,codes(result));return result
    def change_receipt(self,fn):
        raw=loads((self.root/self.r.sandbox_evidence.path).read_bytes());fn(raw);return attach(self.r,self.root,raw)
    def test_clean_code_never_full_security_pass(self):
        result=run(self.r,self.root,self.p);self.assertEqual(result.reports[0].status,'CHECKS_PASSED');self.assertEqual(result.status,'REVIEW_REQUIRED');self.assertFalse(result.to_dict()['hostile_code_execution_certified'])
    def test_unsigned_requires_authorization(self):self.check('SEC_AUTHORIZATION_REQUIRED',reviews=())
    def test_test_only_not_authority(self):self.check('SEC_AUTHORIZATION_REQUIRED',verifier=ReviewVerifier((replace(KEY,assurance='test_only'),)))
    def test_revoked_key(self):self.check('SEC_AUTHORIZATION_REQUIRED',verifier=ReviewVerifier((replace(KEY,enabled=False),)))
    def test_unknown_key(self):self.check('SEC_AUTHORIZATION_REQUIRED',verifier=ReviewVerifier())
    def test_review_rejected(self):self.assertEqual(self.check('SEC_REVIEW_REJECTED',reviews=signed(self.r,self.p,verdict='REJECTED')).status,'BLOCKED')
    def test_uncertain(self):self.check('SEC_AUTHORIZATION_REQUIRED',reviews=signed(self.r,self.p,verdict='UNCERTAIN'))
    def test_bad_signature(self):self.check('SEC_AUTHORIZATION_REQUIRED',reviews=tuple(replace(r,signature='0'*64) for r in signed(self.r,self.p)))
    def test_duplicate_review(self):
        rs=signed(self.r,self.p)
        with self.assertRaises(ContractError):run(self.r,self.root,self.p,reviews=rs+(rs[0],))
    def test_stale_review(self):self.check('SEC_AUTHORIZATION_REQUIRED',as_of=NOW+200)
    def test_future_review(self):self.check('SEC_AUTHORIZATION_REQUIRED',as_of=NOW-4)
    def test_snapshot_binding(self):self.check('SEC_SNAPSHOT_BINDING',p=replace(self.p,snapshot_digest='b'*64))
    def test_no_receipt(self):
        (self.root/self.r.sandbox_evidence.path).unlink();self.check('SEC_SANDBOX_EVIDENCE_MISSING',r=replace(self.r,sandbox_evidence=None))
    def test_bytes_changed(self):
        (self.root/self.r.snapshot.artifacts[0].path).write_bytes(b'changed')
        self.assertEqual(run(self.r,self.root,self.p).status,'BLOCKED')
    def test_extra_file(self):
        (self.root/'hidden.py').write_text('print(1)');self.check('AUDIT_SNAPSHOT_FILE_SET')
    def test_missing_file(self):
        (self.root/self.r.snapshot.artifacts[0].path).unlink();self.check('AUDIT_SNAPSHOT_FILE_SET')
    def test_symlink_source(self):
        a=self.r.snapshot.artifacts[0];path=self.root/a.path;data=path.read_bytes();path.unlink();other=Path(self.tmp.name)/'other';other.write_bytes(data);path.symlink_to(other);self.check('AUDIT_UNSAFE_ENTRY')
    def test_hardlink_source(self):
        a=self.r.snapshot.artifacts[0];os.link(self.root/a.path,Path(self.tmp.name)/'linked');self.check('AUDIT_UNSAFE_ENTRY')
    def test_root_symlink(self):
        link=Path(self.tmp.name)/'link';link.symlink_to(self.root,target_is_directory=True);self.assertEqual(run(self.r,link,self.p).status,'BLOCKED')
    def test_omitted_executable(self):
        a=ref(self.root,'hidden','generated/hidden.sh',b'echo hidden');snap=replace(self.r.snapshot,artifacts=self.r.snapshot.artifacts+(a,));r=replace(self.r,snapshot=snap);r=attach(r,self.root,synthetic_receipt(snap.content_digest));self.check('SEC_EXECUTABLE_INVENTORY_GAP',r=r,p=replace(self.p,snapshot_digest=snap.content_digest))
    def test_wrong_unit_id(self):self.check('SEC_SCOPE_IDENTITY',p=replace(self.p,units=(CodeUnit('unknown','PYTHON','PURE'),)))
    def test_source_limit(self):self.check('SEC_SOURCE_LIMIT',p=replace(self.p,max_source_bytes=2))
    def test_ast_limit(self):self.check('SEC_AST_LIMIT',p=replace(self.p,max_ast_nodes=1))
    def test_report_deterministic(self):self.assertEqual(run(self.r,self.root,self.p).to_dict(),run(self.r,self.root,self.p).to_dict())
    def test_all_bytes_inspected(self):self.assertEqual(set(run(self.r,self.root,self.p).reports[0].inspected_artifact_ids),{a.artifact_id for a in self.r.snapshot.artifacts}|{'sandbox'})
    def test_task_ids(self):self.assertEqual([r.task_id for r in run(self.r,self.root,self.p).reports],['BIE-QA-SEC-001','BIE-QA-SEC-002'])
    def test_actual_probes_not_native_candidate(self):self.check('SEC_NATIVE_GENERATED_RUNTIME_PENDING')
    def test_receipt_snapshot(self):self.check('SEC_SANDBOX_SNAPSHOT',r=self.change_receipt(lambda x:x.update(snapshot_digest='b'*64)))
    def test_receipt_stale(self):self.check('SEC_SANDBOX_TIME',r=self.change_receipt(lambda x:x.update(started_at=1,finished_at=2)))
    def test_receipt_future(self):self.check('SEC_SANDBOX_TIME',r=self.change_receipt(lambda x:x.update(finished_at=NOW+5)))
    def test_receipt_time_reverse(self):self.check('SEC_SANDBOX_TIME',r=self.change_receipt(lambda x:x.update(finished_at=NOW-10)))
    def test_receipt_elapsed(self):self.check('SEC_SANDBOX_TIME',r=self.change_receipt(lambda x:x.update(started_at=NOW-100)))
    def test_receipt_worker(self):self.check('SEC_PROBE_WORKER_IDENTITY',r=self.change_receipt(lambda x:x.update(worker_sha256='b'*64)))
    def test_receipt_false_acceptance(self):self.check('SEC_SANDBOX_OVERCLAIM',r=self.change_receipt(lambda x:x.update(product_accepted=True)))
    def test_receipt_candidate_claim(self):self.check('SEC_SANDBOX_OVERCLAIM',r=self.change_receipt(lambda x:x.update(candidate_executed=True)))
    def test_receipt_fake_backend(self):self.check('SEC_SANDBOX_PROFILE',r=self.change_receipt(lambda x:x.update(profile='node-vm')))
    def test_receipt_canary_modified(self):self.check('SEC_OUTSIDE_CANARY_CHANGED',r=self.change_receipt(lambda x:x.update(outside_canary_unchanged=False)))
    def test_receipt_not_run(self):self.check('SEC_BOUNDARY_NOT_PASSED',r=self.change_receipt(lambda x:x.update(status='NOT_RUN')))
    def test_missing_process(self):self.check('SEC_PROCESS_COVERAGE',r=self.change_receipt(lambda x:x['processes'].pop()))
    def test_duplicate_case(self):self.check('SEC_PROCESS_CASE',r=self.change_receipt(lambda x:x['processes'].__setitem__(1,copy.deepcopy(x['processes'][0]))))
    def test_process_id_replay(self):self.check('SEC_REPLAYED_PROCESS',r=self.change_receipt(lambda x:x['processes'][1].update(execution_id=x['processes'][0]['execution_id'])))
    def test_process_failed(self):self.check('SEC_PROBE_EXIT',r=self.change_receipt(lambda x:x['processes'][0].update(exit_code=1)))
    def test_bool_exit_not_zero(self):self.check('SEC_PROBE_EXIT',r=self.change_receipt(lambda x:x['processes'][0].update(exit_code=False)))
    def test_log_tamper(self):self.check('SEC_PROBE_LOG_IDENTITY',r=self.change_receipt(lambda x:x['processes'][0].update(stdout='forged')))
    def test_child_without_log_change(self):self.check('SEC_CHILD_LOG_MISMATCH',r=self.change_receipt(lambda x:x['processes'][0]['receipt'].update(case='other')))
    def test_nonce_replay(self):self.check('SEC_NONCE_REPLAY',r=self.change_receipt(lambda x:rewrite_child(x,1,lambda c:c.update(nonce='1'*32))))
    def test_missing_control(self):self.check('SEC_CONTROL_COVERAGE',r=self.change_receipt(lambda x:rewrite_child(x,0,lambda c:c['controls'].pop('seccomp_filter'))))
    def test_disabled_control(self):self.check('SEC_CONTROL_NOT_ENFORCED',r=self.change_receipt(lambda x:rewrite_child(x,0,lambda c:c['controls'].update(seccomp_filter=False))))
    def test_truthy_not_boolean_control(self):self.check('SEC_CONTROL_NOT_ENFORCED',r=self.change_receipt(lambda x:rewrite_child(x,0,lambda c:c['controls'].update(non_root=1))))
    def test_missing_probe(self):self.check('SEC_PROBE_COVERAGE',r=self.change_receipt(lambda x:rewrite_child(x,0,lambda c:c['observations'].pop())))
    def test_duplicate_probe(self):self.check('SEC_PROBE_DUPLICATE_OR_UNKNOWN',r=self.change_receipt(lambda x:rewrite_child(x,0,lambda c:c['observations'].__setitem__(1,dict(c['observations'][0])))))
    def test_false_pass_cannot_override_probe(self):self.check('SEC_BOUNDARY_PROBE_FAILED',r=self.change_receipt(lambda x:rewrite_child(x,0,lambda c:c['observations'][8].update(observed='ALLOWED',errno=0))))
    def test_wrong_denial_reason(self):self.check('SEC_BOUNDARY_PROBE_FAILED',r=self.change_receipt(lambda x:rewrite_child(x,0,lambda c:c['observations'][8].update(errno=2))))
    def test_positive_control_must_succeed(self):self.check('SEC_BOUNDARY_PROBE_FAILED',r=self.change_receipt(lambda x:rewrite_child(x,0,lambda c:c['observations'][0].update(observed='DENIED',errno=1))))
    def test_aggregate_tamper(self):self.check('SEC_PROBE_AGGREGATE_MISMATCH',r=self.change_receipt(lambda x:x.update(observations=[])))
    def test_extra_receipt_field(self):self.check('SEC_SANDBOX_FIELDS',r=self.change_receipt(lambda x:x.update(safety=True)))
    def test_contract_codec(self):
        self.assertEqual(decode(loads(canonical_bytes(asdict(self.r))),SecurityRequest),self.r);self.assertEqual(decode(loads(canonical_bytes(asdict(self.p))),SecurityPolicy),self.p)
    def test_unknown_contract_field(self):
        d=asdict(self.p);d['allow_network']=True
        with self.assertRaises(ContractError):decode(d,SecurityPolicy)
    def test_profile_language_mismatch(self):
        with self.assertRaises(ContractError):CodeUnit('a','PYTHON','DATA')
    def test_duplicate_units(self):
        with self.assertRaises(ContractError):replace(self.p,units=self.p.units*2)
    def test_bool_limit(self):
        with self.assertRaises(ContractError):replace(self.p,max_ast_nodes=True)
    def test_dependency_version_range(self):
        with self.assertRaises(ContractError):Dependency('test','^1.2.3','dep')
    def test_parser_hash_pair(self):
        with self.assertRaises(ContractError):replace(self.p,parser_node_sha256='a'*64)
    def test_empty_scope(self):
        with self.assertRaises(ContractError):replace(self.p,units=())
    def test_receipt_alias(self):
        with self.assertRaises(ContractError):replace(self.r,sandbox_evidence=replace(self.r.sandbox_evidence,path=self.r.snapshot.artifacts[0].path))
    def test_bridge_no_pass(self):
        c=ReleaseCandidate('2.0.0','candidate',self.r.snapshot.run_id,self.r.snapshot.revision,self.r.snapshot.artifacts)
        prepared=prepare_release_evidence(self.r,self.root,self.p,c,as_of=NOW)
        self.assertEqual(prepared.envelope.status,'NOT_RUN')
    def test_release_stays_blocked(self):
        c=ReleaseCandidate('2.0.0','candidate',self.r.snapshot.run_id,self.r.snapshot.revision,self.r.snapshot.artifacts)
        q=prepare_release_evidence(self.r,self.root,self.p,c,as_of=NOW)
        path=self.root/q.envelope.report.path;path.parent.mkdir(parents=True);path.write_bytes(q.report_bytes)
        b=EvidenceBundle('2.0.0',c,(q.envelope,))
        report=ReleaseEvaluator().evaluate(b,self.root,as_of=NOW);self.assertFalse(report.release_authorized);self.assertFalse(report.product_accepted)
    def test_cli_unsigned(self):
        base=Path(self.tmp.name);(base/'r.json').write_bytes(canonical_bytes(asdict(self.r)));(base/'p.json').write_bytes(canonical_bytes(asdict(self.p)))
        p=subprocess.run([sys.executable,'-B','-m','bie.qa.security_v2','--request',str(base/'r.json'),'--policy',str(base/'p.json'),'--root',str(self.root),'--as-of',str(NOW)],capture_output=True,text=True)
        self.assertEqual(p.returncode,3,p.stderr);self.assertEqual(json.loads(p.stdout)['status'],'REVIEW_REQUIRED')

class ScannerTests(unittest.TestCase):
    def py(self,s,profile='PURE'):return {x['code'] for x in scan_python(s,profile,20000)[0]}
    def test_python_good_arithmetic(self):self.assertEqual(self.py('def add(a,b):\n return a+b\n'),set())
    def test_python_inert_string(self):self.assertEqual(self.py('message = "eval and open are discussed here"'),set())
    def test_python_comments_not_execution(self):self.assertEqual(self.py('# eval(1)\nvalue = 5'),set())
    def test_python_syntax(self):self.assertIn('SEC_PARSE_ERROR',self.py('def'))
    def test_python_unknown_general_review(self):self.assertIn('SEC_GENERAL_CODE_REVIEW',self.py('a=3','REVIEW'))
    def test_python_builtin_shadow(self):self.assertIn('SEC_BUILTIN_SHADOW',self.py('def f(abs):\n return abs(1)'))
    def test_python_attribute_blocks_pure(self):self.assertIn('SEC_PURE_PROFILE_VIOLATION',self.py('a = b.real'))
    def test_python_import_blocks_pure(self):self.assertIn('SEC_PURE_PROFILE_VIOLATION',self.py('import math'))
    def test_manifest_script_rejected(self):self.assertIn('SEC_UNAPPROVED_INSTALL_OR_BUILD_SCRIPT',{x['code'] for x in scan_manifest('{"scripts":{"postinstall":"bad"}}',(),())[0]})
    def test_manifest_exact_script_still_review(self):self.assertIn('SEC_APPROVED_SCRIPTS_STILL_REQUIRE_ISOLATION',{x['code'] for x in scan_manifest('{"scripts":{"build":"tsc"}}',(),(('build','tsc'),))[0]})
    def test_manifest_unpinned(self):self.assertIn('SEC_UNPINNED_DEPENDENCY',{x['code'] for x in scan_manifest('{"dependencies":{"react":"^19.0.0"}}',(Dependency('react','19.0.0','dep'),),())[0]})
    def test_manifest_duplicate_key(self):self.assertIn('SEC_MANIFEST_PARSE',{x['code'] for x in scan_manifest('{"name":"a","name":"b"}',(),())[0]})
    def test_manifest_workspace_review(self):self.assertIn('SEC_MANIFEST_CAPABILITY_REVIEW',{x['code'] for x in scan_manifest('{"workspaces":["packages/*"]}',(),())[0]})
    def test_manifest_empty_object_allowed(self):self.assertEqual(scan_manifest('{}',(),())[0],[])
    def test_manifest_exact_dependency(self):self.assertEqual(scan_manifest('{"dependencies":{"react":"19.0.0"}}',(Dependency('react','19.0.0','dep'),),())[0],[])
    def test_manifest_nonobject(self):self.assertIn('SEC_MANIFEST_OBJECT',{x['code'] for x in scan_manifest('[]',(),())[0]})
    def test_typescript_data(self):self.assertEqual(scan_typescript('export const n={a:1,b:[true,"ok"]} as const;','TYPESCRIPT','DATA',20000,tools())[0],[])
    def test_typescript_inert_string(self):self.assertEqual(scan_typescript('export const message="eval";','TYPESCRIPT','DATA',20000,tools())[0],[])
    def test_typescript_parse_errors(self):self.assertIn('SEC_PARSE_ERROR',{x['code'] for x in scan_typescript('export const = ;','TYPESCRIPT','DATA',20000,tools())[0]})
    def test_typescript_computed_code(self):self.assertIn('SEC_DATA_PROFILE_VIOLATION',{x['code'] for x in scan_typescript('export const v=1+2;','TYPESCRIPT','DATA',20000,tools())[0]})
    def test_typescript_duplicate_key(self):self.assertIn('SEC_DATA_PROFILE_VIOLATION',{x['code'] for x in scan_typescript('export const v={a:1,a:2};','TYPESCRIPT','DATA',20000,tools())[0]})
    def test_typescript_import_returned(self):self.assertEqual(scan_typescript('import {x} from "./other"; export const a=x;','TYPESCRIPT','REVIEW',20000,tools())[1],['./other'])
    def test_typescript_missing_parser(self):
        with self.assertRaises(ContractError):scan_typescript('export const v=1;','TYPESCRIPT','DATA',20000,None)
    def test_typescript_tool_modified(self):
        t=replace(tools(),typescript_sha256='0'*64)
        with self.assertRaises(ContractError):scan_typescript('export const v=1;','TYPESCRIPT','DATA',20000,t)

# Each case is an individually named unit test, not an inflated subtest count.
PY_ATTACKS={
 'eval':'x=eval("1")','exec':'exec("x=1")','import_os':'import os','from_socket':'from socket import socket','dunder':'x=a.__class__','builtins_alias':'import builtins as b',
 'getattr':'x=getattr(a,"x")','decorator':'@decorator\ndef f():\n return 1','with':'with thing: pass','class':'class C: pass','comprehension':'x=[n for n in a]',
 'lambda':'x=lambda a:a','while':'while True: pass','loop':'for x in a: pass','try':'try:\n x=1\nexcept: pass','yield':'def f():\n yield 1',
 'await':'async def f():\n return 1','attribute_call':'a.method()','indirect_call':'f(1)','star_call':'f(*x)'}
for name,source in PY_ATTACKS.items():
 def test(self,source=source):self.assertTrue(self.py(source),'Expected a blocker or review for unsupported capability')
 setattr(ScannerTests,'test_py_'+name,test)
TS_ATTACKS={
 'eval':'ev\\u0061l("1")','function':'new Function("return 1")','process':'const p=process;','require':'require("node:fs")','dynamic_import':'import("./x")',
 'prototype':'a["constructor"]','dynamic_property':'a[b]','spread':'export const a={...b};','getter':'export const a={get x(){return 1;}};',
 'template':'export const a=`${call()}`;','raw_html':'const a=<div dangerouslySetInnerHTML={{__html:"x"}}/>;','global':'globalThis["eval"]("1")','fetch':'fetch("https://example.invalid")'}
for name,source in TS_ATTACKS.items():
 def test(self,source=source):self.assertTrue(scan_typescript(source,'TSX','DATA',20000,tools())[0])
 setattr(ScannerTests,'test_ts_'+name,test)

class IntegrationTests(unittest.TestCase):
    def test_actual_fixed_boundary_probes(self):
        result=collect_boundary('b'*64)
        self.assertEqual(result['status'],'CHECKS_PASSED',result)
        self.assertEqual(len(result['observations']),18);self.assertFalse(result['candidate_executed'])
        self.assertEqual(inspect_sandbox(result,'b'*64,result['finished_at'],3600)['fixed_probe_processes'],3)
    def test_collector_timeout_contract(self):
        with self.assertRaises(ContractError):collect_boundary('a'*64,timeout=0)

class CodeScopeTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'snapshot'
    def evaluate_code(self,code,language='PYTHON',profile='PURE',**kw):
        r,p,t=fixture(self.root,language,profile,code);return run(r,self.root,p,t,**kw)
    def test_empty_source(self):self.assertIn('SEC_EMPTY_SOURCE',codes(self.evaluate_code(b'  \n')))
    def test_non_utf8(self):self.assertIn('SEC_SOURCE_UTF8',codes(self.evaluate_code(b'\xff')))
    def test_null(self):self.assertIn('SEC_HIDDEN_CONTROL',codes(self.evaluate_code(b'x=1\x00')))
    def test_bidi(self):self.assertIn('SEC_HIDDEN_CONTROL',codes(self.evaluate_code('x="\u202e"'.encode())))
    def test_typescript_evaluator(self):self.assertNotIn('SEC_DATA_PROFILE_VIOLATION',codes(self.evaluate_code(b'export const a=1;','TYPESCRIPT','DATA')))
    def test_unapproved_import(self):self.assertIn('SEC_UNAPPROVED_IMPORT',codes(self.evaluate_code(b'import {x} from "unapproved";','TYPESCRIPT','REVIEW')))
    def test_missing_relative_import(self):self.assertIn('SEC_IMPORT_CLOSURE',codes(self.evaluate_code(b'import {x} from "./other";','TYPESCRIPT','REVIEW')))
    def test_escape_import(self):self.assertIn('SEC_IMPORT_PATH_ESCAPE',codes(self.evaluate_code(b'import {x} from "../../escape";','TYPESCRIPT','REVIEW')))
    def test_wrong_tool_hash(self):
        r,p,t=fixture(self.root,'TYPESCRIPT','DATA',b'export const a=1;');t=replace(t,node_sha256='a'*64)
        self.assertIn('SEC_PARSER_POLICY_BINDING',codes(run(r,self.root,p,t)))
    def test_missing_parser_evaluator(self):
        r,p,t=fixture(self.root,'TYPESCRIPT','DATA',b'export const a=1;');self.assertIn('SEC_TYPESCRIPT_PARSER_REQUIRED',codes(run(r,self.root,p)))
    def test_language_path_mismatch(self):
        r,p,t=fixture(self.root);p=replace(p,units=(CodeUnit('code','TYPESCRIPT','DATA'),));self.assertIn('SEC_LANGUAGE_PATH_MISMATCH',codes(run(r,self.root,p)))
    def test_dependency_is_not_security_clearance(self):
        r,p,t=fixture(self.root,'TYPESCRIPT','REVIEW',b'import {x} from "react";');a=ref(self.root,'dep','deps/react.txt',b'SYNTHETIC dependency bytes');snap=replace(r.snapshot,artifacts=r.snapshot.artifacts+(a,));r=replace(r,snapshot=snap);r=attach(r,self.root,synthetic_receipt(snap.content_digest));p=replace(p,snapshot_digest=snap.content_digest,dependencies=(Dependency('react','19.0.0','dep'),))
        result=run(r,self.root,p,t);self.assertIn('SEC_TRANSITIVE_AND_VULNERABILITY_REVIEW',codes(result));self.assertNotIn('SEC_UNAPPROVED_IMPORT',codes(result))
    def test_local_module_closure(self):
        r,p,t=fixture(self.root,'TYPESCRIPT','REVIEW',b'import {x} from "./other";');a=ref(self.root,'other','generated/other.ts',b'export const x=2;');snap=replace(r.snapshot,artifacts=r.snapshot.artifacts+(a,));r=replace(r,snapshot=snap);r=attach(r,self.root,synthetic_receipt(snap.content_digest));p=replace(p,snapshot_digest=snap.content_digest,units=p.units+(CodeUnit('other','TYPESCRIPT','DATA'),))
        self.assertNotIn('SEC_IMPORT_CLOSURE',codes(run(r,self.root,p,t)))
    def test_missing_dependency_bytes(self):
        r,p,t=fixture(self.root);p=replace(p,dependencies=(Dependency('react','19.0.0','none'),));self.assertIn('SEC_SCOPE_IDENTITY',codes(run(r,self.root,p)))
    def test_code_dependency_alias(self):
        r,p,t=fixture(self.root);p=replace(p,dependencies=(Dependency('react','19.0.0','code'),));self.assertIn('SEC_SCOPE_IDENTITY',codes(run(r,self.root,p)))
    def test_inert_manifest(self):self.assertEqual(self.evaluate_code(b'{"name":"fixture"}','NPM_MANIFEST','MANIFEST').reports[0].status,'CHECKS_PASSED')
    def test_receipt_codec_optional_none(self):
        r,p,t=fixture(self.root,receipt=False);self.assertEqual(decode(loads(canonical_bytes(asdict(r))),SecurityRequest),r)
    def test_overwrite_cli_blocked(self):
        r,p,t=fixture(self.root);base=Path(self.tmp.name);(base/'r.json').write_bytes(canonical_bytes(asdict(r)));(base/'p.json').write_bytes(canonical_bytes(asdict(p)));out=base/'already.json';out.write_bytes(b'preserve')
        proc=subprocess.run([sys.executable,'-B','-m','bie.qa.security_v2','--request',str(base/'r.json'),'--policy',str(base/'p.json'),'--root',str(self.root),'--as-of',str(NOW),'--output',str(out)],capture_output=True)
        self.assertEqual(proc.returncode,4);self.assertEqual(out.read_bytes(),b'preserve')

for suffix in ('html','svg','css','node','wasm','exe'):
    def test(self,suffix=suffix):
        r,p,t=fixture(self.root);a=ref(self.root,'active','generated/active.'+suffix,b'SYNTHETIC unsupported active content');snap=replace(r.snapshot,artifacts=r.snapshot.artifacts+(a,));r=replace(r,snapshot=snap);r=attach(r,self.root,synthetic_receipt(snap.content_digest));p=replace(p,snapshot_digest=snap.content_digest)
        self.assertIn('SEC_EXECUTABLE_INVENTORY_GAP',codes(run(r,self.root,p)))
    setattr(CodeScopeTests,'test_omitted_active_'+suffix,test)

class SchemaTests(unittest.TestCase):
    def test_schema_request(self):
        import jsonschema
        with tempfile.TemporaryDirectory() as d:
            r,p,t=fixture(Path(d)/'s');path=Path(__file__).resolve().parents[2]/'docs/qa_section16/batch020/request.schema.json';jsonschema.Draft202012Validator(json.loads(path.read_text())).validate(json.loads(canonical_bytes(asdict(r))))
    def test_schema_policy(self):
        import jsonschema
        with tempfile.TemporaryDirectory() as d:
            r,p,t=fixture(Path(d)/'s');path=Path(__file__).resolve().parents[2]/'docs/qa_section16/batch020/policy.schema.json';jsonschema.Draft202012Validator(json.loads(path.read_text())).validate(json.loads(canonical_bytes(asdict(p))))
    def test_schema_result(self):
        import jsonschema
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'s';r,p,t=fixture(root);v=run(r,root,p);path=Path(__file__).resolve().parents[2]/'docs/qa_section16/batch020/result_record.schema.json';jsonschema.Draft202012Validator(json.loads(path.read_text())).validate(json.loads(canonical_bytes(asdict(v))))
