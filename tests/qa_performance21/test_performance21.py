import unittest,tempfile,copy,json,hashlib,hmac,sys,time,os,subprocess
from pathlib import Path
from dataclasses import replace,asdict
from fractions import Fraction
from unittest.mock import patch
from performance21_support import *
from bie.qa.release_v2.contracts import ContractError,ReleaseCandidate
from bie.qa.performance_v2.metrics import percentile,ratio,concurrent_peak,summarize
from bie.qa.performance_v2.codec import decode,loads
from bie.qa.performance_v2.evaluator import inspect_output,read_log

class Contracts(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.r,self.p,self.raw=fixture(self.root)
    def tearDown(self):self.t.cleanup()
    def test_round_trip_request(self):self.assertEqual(decode(loads(canonical_bytes(asdict(self.r))),PerformanceRequest),self.r)
    def test_round_trip_policy(self):self.assertEqual(decode(loads(canonical_bytes(asdict(self.p))),PerformancePolicy),self.p)
    def test_unknown_json_field(self):
        d=asdict(self.r);d['command']='no'
        with self.assertRaises(ContractError):decode(loads(canonical_bytes(d)),PerformanceRequest)
    def test_duplicate_json_keys(self):
        with self.assertRaises(ContractError):loads(b'{"a":1,"a":2}')
    def test_snapshot_binding(self):self.assertIn('PERF_SNAPSHOT_BINDING',codes(run(self.r,self.root,replace(self.p,snapshot_digest='f'*64))))
    def test_request_evidence_alias(self):
        with self.assertRaises(ContractError):replace(self.r,evidence=self.r.evidence+(self.r.snapshot.artifacts[0],))
    def test_request_missing_receipt(self):
        with self.assertRaises(ContractError):replace(self.r,receipt_id='missing')
    def test_job_duplicate(self):
        with self.assertRaises(ContractError):replace(self.p,jobs=(self.p.jobs[0],)*2)
    def test_output_id_length(self):
        with self.assertRaises(ContractError):replace(self.p.jobs[0].outputs[0],output_id='x'*25)
    def test_policy_unused_producer(self):
        with self.assertRaises(ContractError):replace(self.p,producer_bindings=self.p.producer_bindings+(('unused','c'*64),))
    def test_fractional_fps_allowed(self):self.assertEqual(OutputSpec('m','outputs/m.mp4','MP4',width=16,height=16,frames=3,fps_numerator=30000,fps_denominator=1001).fps_numerator,30000)
    def test_noncanonical_fps(self):
        with self.assertRaises(ContractError):OutputSpec('m','outputs/m.mp4','MP4',width=16,height=16,frames=3,fps_numerator=60,fps_denominator=2)
    def test_data_needs_golden(self):
        with self.assertRaises(ContractError):OutputSpec('b','outputs/b.bin','BYTES')
    def test_render_decode_budget(self):
        with self.assertRaises(ContractError):OutputSpec('m','outputs/m.mp4','MP4',width=4096,height=4096,frames=100,fps_numerator=30)
    def test_input_missing(self):
        p=replace(self.p,jobs=(replace(self.p.jobs[0],input_ids=('missing',)),self.p.jobs[1]))
        self.assertIn('PERF_INPUT_INVENTORY',codes(run(self.r,self.root,p)))
    def test_root_alias(self):
        link=self.root.parent/(self.root.name+'-link');link.symlink_to(self.root)
        try:self.assertEqual(run(self.r,link,self.p).status,'BLOCKED')
        finally:link.unlink()
    def test_unused_evidence(self):
        a=ref(self.root,'extra','extra.txt',b'EXTRA','report');r=replace(self.r,evidence=self.r.evidence+(a,))
        self.assertIn('PERF_EVIDENCE_INVENTORY',codes(run(r,self.root,self.p)))
    def test_extra_files(self):
        (self.root/'extra').write_bytes(b'EXTRA');self.assertIn('AUDIT_SNAPSHOT_FILE_SET',codes(run(self.r,self.root,self.p)))
    def test_actual_byte_tamper(self):
        (self.root/'evidence/first/result.bin').write_bytes(b'wrong');self.assertEqual(run(self.r,self.root,self.p).status,'BLOCKED')
    def test_hardlink(self):
        f=self.root/'evidence/first/result.bin';os.link(f,self.root/'copy')
        self.assertEqual(run(self.r,self.root,self.p).status,'BLOCKED')

# Each name below exercises a distinct declared field boundary, counted once.
def _bad_policy(field,value):
    def test(self):
        with self.assertRaises(ContractError):replace(self.p,**{field:value})
    return test
for field,value in [('max_workers',0),('max_workers',True),('max_workers',5),('timeout_ms',0),('max_rss_bytes',0),('address_space_bytes',1),('address_space_bytes',2**34),('min_render_fps_milli',0),('min_jobs_per_second_milli',-1),('max_total_output_bytes',0),('max_file_bytes',0),('max_receipt_age_seconds',0),('environment_digest','bad'),('max_batch_ms',1.1)]:
    setattr(Contracts,'test_invalid_'+field+'_'+str(value).replace('.','_').replace('-','neg'),_bad_policy(field,value))

class Metrics(unittest.TestCase):
    def test_nearest_rank(self):self.assertEqual(percentile(list(range(1,101))),95)
    def test_single(self):self.assertEqual(percentile([12]),12)
    def test_percentile_small_tail(self):self.assertEqual(percentile([1,100]),100)
    def test_empty(self):
        with self.assertRaises(ContractError):percentile([])
    def test_bool_rejected(self):
        with self.assertRaises(ContractError):percentile([True])
    def test_touching_not_concurrent(self):self.assertEqual(concurrent_peak([(0,2),(2,3)]),1)
    def test_overlap(self):self.assertEqual(concurrent_peak([(0,10),(1,3),(2,5)]),3)
    def test_bad_interval(self):
        with self.assertRaises(ContractError):concurrent_peak([(2,1)])
    def test_exact_ratio(self):self.assertEqual(ratio(10,20),{'numerator':1,'denominator':2})
    def test_zero_denominator(self):
        with self.assertRaises(ContractError):ratio(1,0)
    def test_latency_includes_queue(self):
        j=[dict(enqueue_ns=0,dispatch_ns=10,complete_ns=100)]
        self.assertEqual(summarize(j,0,100,1)['p95_latency_ns'],100)
    def test_throughput_not_sum_service(self):
        j=[dict(enqueue_ns=0,dispatch_ns=0,complete_ns=10**9),dict(enqueue_ns=0,dispatch_ns=0,complete_ns=10**9)]
        self.assertEqual(summarize(j,0,10**9,2)['verified_jobs_per_second'],{'numerator':2,'denominator':1})
    def test_failed_jobs_not_counted_success(self):
        j=[dict(enqueue_ns=0,dispatch_ns=0,complete_ns=10**9)]
        self.assertEqual(summarize(j,0,10**9,0)['verified_jobs_per_second']['numerator'],0)
    def test_empty_queue(self):
        with self.assertRaises(ContractError):summarize([],0,1,0)

# Independent fixtures rather than duplicating inherited test methods.
class Evidence(unittest.TestCase):
    setUp=Contracts.setUp;tearDown=Contracts.tearDown
    def test_healthy_is_review_not_release(self):self.assertEqual(run(self.r,self.root,self.p).status,'REVIEW_REQUIRED')
    def test_healthy_jobs_verified(self):self.assertEqual(json.loads(run(self.r,self.root,self.p).details_json)['metrics']['verified_successes'],2)
    def test_unsigned_auth_required(self):self.assertIn('PERF_AUTHORIZATION_REQUIRED',codes(run(self.r,self.root,self.p,reviews=())))
    def test_rejected_auth_blocks(self):self.assertIn('PERF_REVIEW_REJECTED',codes(run(self.r,self.root,self.p,reviews=signed(self.r,self.p,verdict='REJECTED'))))
    def test_test_only_cannot_authorize(self):
        k=replace(KEY,assurance='test_only');self.assertIn('PERF_AUTHORIZATION_REQUIRED',codes(run(self.r,self.root,self.p,reviews=signed(self.r,self.p,key=k),verifier=ReviewVerifier((k,)))))
    def test_stale_auth(self):
        reviews=signed(self.r,self.p);self.assertIn('PERF_AUTHORIZATION_REQUIRED',codes(run(self.r,self.root,self.p,reviews=reviews,as_of=NOW+120)))
    def test_bad_signature(self):
        rr=tuple(replace(r,signature='0'*64) for r in signed(self.r,self.p));self.assertIn('PERF_AUTHORIZATION_REQUIRED',codes(run(self.r,self.root,self.p,reviews=rr)))
    def test_unknown_review(self):
        rr=(replace(signed(self.r,self.p)[0],subject_id='arbitrary'),)
        self.assertIn('PERF_UNEXPECTED_REVIEW',codes(run(self.r,self.root,self.p,reviews=rr)))
    def test_duplicate_review_rejected(self):
        rr=signed(self.r,self.p)
        with self.assertRaises(ContractError):run(self.r,self.root,self.p,reviews=(rr[0],rr[0]))
    def test_no_evidence(self):
        for a in self.r.evidence:(self.root/a.path).unlink()
        self.assertIn('PERF_EXECUTION_MISSING',codes(run(PerformanceRequest(self.r.snapshot),self.root,self.p)))
    def test_wrong_output_rehashed(self):
        r=rewrite(self.r,self.root,'first-result',b'wrong')
        self.assertIn('PERF_GOLDEN_OUTPUT_MISMATCH',codes(run(r,self.root,self.p)))
    def test_log_hex(self):self.assertEqual(read_log(canonical_bytes({'encoding':'hex','data':'000aff'})),b'\0\n\xff')
    def test_log_whitespace_not_normalized(self):
        with self.assertRaises(ContractError):read_log(canonical_bytes({'encoding':'hex','data':'00 ff'}))
    def test_unknown_log_encoding(self):
        with self.assertRaises(ContractError):read_log(canonical_bytes({'encoding':'utf8','data':'hi'}))
    def test_removed_memory_control(self):
        x=loads((self.root/'evidence/memoryprobe/stdout.json').read_bytes());pr=loads(bytes.fromhex(x['data']));pr['over_limit_denied']=False;x['data']=canonical_bytes(pr).hex()
        r=rewrite(self.r,self.root,'memoryprobe-stdout',canonical_bytes(x))
        self.assertIn('PERF_MEMORY_PROBE_FAILED',codes(run(r,self.root,self.p)))
    def test_changed_limits(self):
        d=loads((self.root/'evidence/first/limits.json').read_bytes());d['address_space']=[2**32]*2
        r=rewrite(self.r,self.root,'first-limits',canonical_bytes(d));self.assertIn('PERF_LIMIT_NOT_ENFORCED',codes(run(r,self.root,self.p)))

def _mutation(fn,code):
    def test(self):
        raw=copy.deepcopy(self.raw);fn(raw);r=rebind(self.r,self.root,raw)
        self.assertIn(code,codes(run(r,self.root,self.p)))
    return test
mutations={
 'schema':(lambda d:d.update(schema_version='other'),'PERF_PROFILE'),
 'profile':(lambda d:d.update(profile='NATIVE'),'PERF_PROFILE'),
 'policy':(lambda d:d.update(policy_digest='a'*64),'PERF_RECEIPT_BINDING'),
 'snapshot':(lambda d:d.update(snapshot_digest='f'*64),'PERF_RECEIPT_BINDING'),
 'claim_acceptance':(lambda d:d.update(product_accepted=True),'PERF_OVERCLAIM'),
 'claim_native':(lambda d:d.update(native_queue_executed=True),'PERF_OVERCLAIM'),
 'execution_id':(lambda d:d.update(execution_id='bad'),'PERF_EXECUTION_ID'),
 'future':(lambda d:d.update(finished_at=NOW+1),'PERF_RECEIPT_TIME'),
 'stale':(lambda d:d.update(started_at=1,finished_at=2),'PERF_RECEIPT_TIME'),
 'environment':(lambda d:d.update(environment_after={'changed':True}),'PERF_ENVIRONMENT_MISMATCH'),
 'collector':(lambda d:d.update(collector_sha256='a'*64),'PERF_INSTRUMENT_IDENTITY'),
 'launcher':(lambda d:d.update(launcher_sha256='a'*64),'PERF_INSTRUMENT_IDENTITY'),
 'probe_hash':(lambda d:d.update(probe_sha256='a'*64),'PERF_INSTRUMENT_IDENTITY'),
 'producer_binding':(lambda d:d.update(producers=[['producer','a'*64]]),'PERF_PRODUCER_IDENTITY'),
 'missing_job':(lambda d:d['jobs'].pop(),'PERF_JOB_COVERAGE'),
 'duplicate_job':(lambda d:d['jobs'].__setitem__(1,d['jobs'][0]),'PERF_JOB_COVERAGE'),
 'job_producer':(lambda d:d['jobs'][0].update(producer_id='other'),'PERF_JOB_PRODUCER'),
 'replay':(lambda d:d['jobs'][0].update(execution_id=d['jobs'][1]['execution_id']),'PERF_EXECUTION_REPLAY'),
 'bad_clock':(lambda d:d['jobs'][0].update(process_end_ns=0),'PERF_CLOCK_ORDER'),
 'bool_clock':(lambda d:d['jobs'][0].update(process_start_ns=True),'INVALID_INTEGER'),
 'exit':(lambda d:d['jobs'][0].update(exit_code=2),'PERF_JOB_FAILED'),
 'timeout':(lambda d:d['jobs'][0].update(timed_out=True),'PERF_TIMEOUT'),
 'changed_input':(lambda d:d['jobs'][0].update(input_unchanged=False),'PERF_INPUT_CHANGED'),
 'issue':(lambda d:d['jobs'][0].update(issues=['SOME_ISSUE']),'PERF_COLLECTOR_ISSUE'),
 'memory_basis':(lambda d:d['jobs'][0].update(memory_basis='PROCESS_TREE'),'PERF_MEMORY_BASIS'),
 'zero_rss':(lambda d:d['jobs'][0].update(peak_rss_bytes=0),'INVALID_INTEGER'),
 'rss':(lambda d:d['jobs'][0].update(peak_rss_bytes=2**30),'PERF_MEMORY_BUDGET'),
 'missing_output':(lambda d:d['jobs'][0].update(outputs={}),'PERF_OUTPUT_COVERAGE'),
 'aliased_output':(lambda d:d['jobs'][0].update(outputs={'result':'source'}),'PERF_OUTPUT_REF'),
 'reused_log':(lambda d:d['jobs'][0].update(stdout_id=d['memory_probe']['stdout_id']),'PERF_LOG_REF'),
 'window_shrink':(lambda d:d.update(queue_start_ns=20000000),'PERF_QUEUE_WINDOW'),
 'window_truncate':(lambda d:d.update(queue_end_ns=40000000),'PERF_QUEUE_WINDOW'),
 'probe_exit':(lambda d:d['memory_probe'].update(exit_code=1),'PERF_MEMORY_PROBE_FAILED'),
 'probe_scope':(lambda d:d['memory_probe'].update(producer_id='unknown'),'PERF_MEMORY_PROBE_SCOPE'),
 'unknown_field':(lambda d:d.update(success=True),'PERF_RECEIPT_FIELDS'),
}
for name,(fn,code) in mutations.items():setattr(Evidence,'test_reject_'+name,_mutation(fn,code))

def _budget(field,value,code):
    def test(self):
        p=replace(self.p,**{field:value});raw=copy.deepcopy(self.raw);raw['policy_digest']=p.content_digest
        r=rebind(self.r,self.root,raw);self.assertIn(code,codes(run(r,self.root,p)))
    return test
for field,value,code in [('max_workers',1,'PERF_CONCURRENCY_EXCEEDED'),('max_job_ms',1,'PERF_JOB_BUDGET'),('max_p95_queue_ms',1,'PERF_QUEUE_LATENCY'),('max_p95_latency_ms',1,'PERF_END_TO_END_LATENCY'),('max_batch_ms',1,'PERF_BATCH_DEADLINE'),('min_jobs_per_second_milli',1000000000,'PERF_THROUGHPUT')]:
    setattr(Evidence,'test_budget_'+field,_budget(field,value,code))

class Runtime(unittest.TestCase):
    def test_real_queue_and_limits(self):
        with tempfile.TemporaryDirectory() as d:
            r,p,prod=real_fixture(d);r=collect(r,d,p,prod);a=evaluate(r,d,p,as_of=int(time.time()))
            self.assertEqual(a.status,'REVIEW_REQUIRED');details=json.loads(a.details_json)
            self.assertEqual(details['metrics']['verified_successes'],2);self.assertTrue(details['memory_probe']['over_limit_denied'])
            self.assertGreater(details['metrics']['makespan_ns'],0)
    def test_real_wrong_output(self):
        with tempfile.TemporaryDirectory() as d:
            r,p,prod=real_fixture(d,b'import sys\nfrom pathlib import Path\nPath(sys.argv[1]).write_bytes(b"wrong")\n',1)
            r=collect(r,d,p,prod);self.assertIn('PERF_GOLDEN_OUTPUT_MISMATCH',codes(evaluate(r,d,p,as_of=int(time.time()))))
    def test_real_timeout(self):
        with tempfile.TemporaryDirectory() as d:
            r,p,prod=real_fixture(d,b'import time\ntime.sleep(2)\n',1);p=replace(p,timeout_ms=150)
            r=collect(r,d,p,prod);self.assertIn('PERF_TIMEOUT',codes(evaluate(r,d,p,as_of=int(time.time()))))
    def test_real_extra_output(self):
        with tempfile.TemporaryDirectory() as d:
            r,p,prod=real_fixture(d,b'import sys\nfrom pathlib import Path\nPath(sys.argv[1]).write_bytes(b"hello")\nPath("untracked").write_bytes(b"extra")\n',1)
            r=collect(r,d,p,prod);self.assertIn('PERF_COLLECTOR_ISSUE',codes(evaluate(r,d,p,as_of=int(time.time()))))
    def test_real_exception(self):
        with tempfile.TemporaryDirectory() as d:
            r,p,prod=real_fixture(d,b'raise ValueError("authored fault")\n',1)
            r=collect(r,d,p,prod);self.assertIn('PERF_JOB_FAILED',codes(evaluate(r,d,p,as_of=int(time.time()))))
    def test_producer_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            r,p,prod=real_fixture(d);wrong=replace(prod[0],executable_sha256='a'*64)
            with self.assertRaises(ContractError):collect(r,d,p,(wrong,))
    def test_environment_mismatch_preflight(self):
        with tempfile.TemporaryDirectory() as d:
            r,p,prod=real_fixture(d)
            with self.assertRaises(ContractError):collect(r,d,replace(p,environment_digest='a'*64),prod)
    def test_relative_producer_rejected(self):
        with self.assertRaises(ContractError):Producer('p','python','a'*64,('-V',))
    def test_receipt_not_executable(self):
        with tempfile.TemporaryDirectory() as d:
            r,p,raw=fixture(d)
            with self.assertRaises(ContractError):collect(r,d,p,())

class BridgeAndCLI(unittest.TestCase):
    setUp=Contracts.setUp;tearDown=Contracts.tearDown
    def test_nonrelease_bridge(self):
        from bie.qa.performance_v2.bridge import prepare_release_evidence
        c=ReleaseCandidate('2.0.0','candidate',self.r.snapshot.run_id,self.r.snapshot.revision,self.r.snapshot.artifacts)
        result=prepare_release_evidence(self.r,self.root,self.p,c,as_of=NOW)
        self.assertEqual(result.envelope.status,'NOT_RUN')
    def test_full_release_stays_blocked(self):
        from bie.qa.performance_v2.bridge import prepare_release_evidence
        from bie.qa.release_v2 import ReleaseEvaluator,EvidenceBundle
        c=ReleaseCandidate('2.0.0','candidate',self.r.snapshot.run_id,self.r.snapshot.revision,self.r.snapshot.artifacts)
        e=prepare_release_evidence(self.r,self.root,self.p,c,as_of=NOW)
        p=self.root/e.envelope.report.path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(e.report_bytes)
        rr=ReleaseEvaluator().evaluate(EvidenceBundle('2.0.0',c,(e.envelope,)),self.root,as_of=NOW)
        self.assertFalse(rr.release_authorized);self.assertFalse(rr.product_accepted)

    def test_cli_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);rp=root/'request.json';pp=root/'policy.json';out=root/'output.json'
            rp.write_bytes(canonical_bytes(asdict(self.r)));pp.write_bytes(canonical_bytes(asdict(self.p)))
            cmd=[sys.executable,'-B','-m','bie.qa.performance_v2',str(rp),str(pp),'--root',str(self.root),'--as-of',str(NOW),'--output',str(out)]
            c=subprocess.run(cmd,capture_output=True,timeout=15)
            self.assertEqual(c.returncode,3,c.stdout.decode()+c.stderr.decode());before=out.read_bytes()
            c=subprocess.run(cmd,capture_output=True,timeout=15);self.assertEqual(c.returncode,4);self.assertEqual(out.read_bytes(),before)
    def test_invalid_cli_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.json';p.write_bytes(b'{}')
            c=subprocess.run([sys.executable,'-B','-m','bie.qa.performance_v2',str(p),str(p),'--root',str(self.root),'--as-of',str(NOW)],capture_output=True,timeout=10)
            self.assertEqual(c.returncode,4)

if __name__=='__main__':unittest.main()

class RenderOutput(unittest.TestCase):
    def data(self):return (Path(__file__).parent/'fixtures/authored.mp4').read_bytes()
    def spec(self):return OutputSpec('movie','outputs/movie.mp4','MP4',width=64,height=48,frames=12,fps_numerator=12)
    def test_actual_mp4(self):self.assertEqual(inspect_output(self.data(),self.spec())['frames'],12)
    def test_short_render_rejected(self):
        with self.assertRaisesRegex(ContractError,'PERF_RENDER_SPEC_MISMATCH'):inspect_output(self.data(),replace(self.spec(),frames=6))
    def test_wrong_fps_rejected(self):
        with self.assertRaisesRegex(ContractError,'PERF_RENDER_SPEC_MISMATCH'):inspect_output(self.data(),replace(self.spec(),fps_numerator=6))
    def test_wrong_dimensions(self):
        with self.assertRaises(ContractError):inspect_output(self.data(),replace(self.spec(),width=32))
    def test_corrupt_media(self):
        with self.assertRaises(ContractError):inspect_output(b'not a video',self.spec())
    def test_empty(self):
        with self.assertRaisesRegex(ContractError,'PERF_EMPTY_OUTPUT'):inspect_output(b'',self.spec())
    def test_wrong_golden(self):
        with self.assertRaisesRegex(ContractError,'PERF_GOLDEN_OUTPUT_MISMATCH'):inspect_output(self.data(),replace(self.spec(),expected_sha256='0'*64))
    def test_render_speed_budget(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);r,p,raw=fixture(root)
            # Authored MP4 bytes, synthetic timing record. No runtime speed claim.
            o=replace(self.spec(),output_id='result',path='outputs/result.mp4')
            p=replace(p,jobs=(replace(p.jobs[0],outputs=(o,)),p.jobs[1]),min_render_fps_milli=1000000000)
            r=rewrite(r,root,'first-result',self.data());r=replace(r,evidence=tuple(replace(a,role='video') if a.artifact_id=='first-result' else a for a in r.evidence))
            raw['policy_digest']=p.content_digest;r=rebind(r,root,raw)
            self.assertIn('PERF_RENDER_SPEED',codes(run(r,root,p)))

class Schemas(unittest.TestCase):
    def validate(self,name,kind):
        import jsonschema
        schema=loads((Path(__file__).resolve().parents[2]/'docs/qa_section16/batch021'/name).read_bytes())
        jsonschema.Draft202012Validator.check_schema(schema)
        with tempfile.TemporaryDirectory() as d:
            r,p,raw=fixture(d);data=loads(canonical_bytes(asdict(r) if kind=='request' else asdict(p) if kind=='policy' else raw))
            jsonschema.validate(data,schema)
            data['unexpected_field']='forbidden'
            with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(data,schema)
    def test_request_schema(self):self.validate('performance_request.schema.json','request')
    def test_policy_schema(self):self.validate('performance_policy.schema.json','policy')
    def test_execution_schema(self):self.validate('performance_execution.schema.json','execution')
