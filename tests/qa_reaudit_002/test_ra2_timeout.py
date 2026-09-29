from ra2_support import *
import performance21_support as pf
from bie.qa.performance_v2.collector import _limit_evidence,collect
from bie.qa.performance_v2.evaluator import evaluate

class TimeoutEvidence(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name);self.path=self.root/'limits.json'
    def failed(self,code,data=None):
        if data is not None:self.path.write_bytes(data)
        issues=[];result=_limit_evidence(self.path,issues)
        self.assertIn(code,issues);value=json.loads(result)
        self.assertEqual(value['status'],'UNAVAILABLE');self.assertTrue(result)
        self.assertNotIn('address_space',value)
        return value
    def test_missing_receipt(self):self.failed('PERF_LIMITS_MISSING')
    def test_empty_receipt(self):self.failed('PERF_LIMITS_EMPTY',b'')
    def test_truncated_receipt(self):self.failed('PERF_LIMITS_MALFORMED',b'{"schema_version":')
    def test_nonobject_receipt(self):self.failed('PERF_LIMITS_MALFORMED',b'[]')
    def test_invalid_utf8_receipt(self):self.failed('PERF_LIMITS_MALFORMED',b'\xff')
    def test_duplicate_keys_receipt(self):self.failed('PERF_LIMITS_MALFORMED',b'{"a":1,"a":2}')
    def test_oversized_receipt(self):self.failed('PERF_LIMITS_OVERSIZED',b'x'*65537)
    def test_linked_receipt_rejected(self):
        other=self.root/'other';other.write_bytes(b'{}');self.path.symlink_to(other);self.failed('PERF_LIMITS_UNSAFE')
    def test_read_failure_preserved(self):
        self.path.write_bytes(b'{}')
        with patch.object(Path,'read_bytes',side_effect=OSError('diagnostic')):self.failed('PERF_LIMITS_UNAVAILABLE')
    def test_valid_receipt_bytes_unchanged(self):
        data=b'{ "schema_version" : "custom-inspected" }\n';self.path.write_bytes(data);issues=[]
        self.assertEqual(_limit_evidence(self.path,issues),data);self.assertFalse(issues)
    def test_failure_witness_preserves_observed_bytes_hash(self):
        import hashlib
        data=b'{';r=self.failed('PERF_LIMITS_MALFORMED',data)
        self.assertEqual(r['raw_bytes'],len(data));self.assertEqual(r['raw_sha256'],hashlib.sha256(data).hexdigest())
    def test_real_timeout_with_empty_file_returns_blocker(self):
        r,p,prods=pf.real_fixture(self.root,body=b'from pathlib import Path\nimport time\nPath("limits.json").write_bytes(b"")\ntime.sleep(4)\n',jobs=1)
        p=replace(p,timeout_ms=700);got=collect(r,self.root,p,prods)
        row=next(a for a in got.evidence if a.artifact_id==got.receipt_id)
        body=json.loads((self.root/row.path).read_text());job=body['jobs'][0]
        self.assertTrue(job['timed_out']);self.assertIn('PERF_PROCESS_TIMEOUT',job['issues'])
        self.assertIn('PERF_LIMITS_EMPTY',job['issues']);self.assertEqual(job['outputs'],{})
        result=evaluate(got,self.root,p,as_of=body['finished_at'],reviews=(),verifier=None)
        self.assertEqual(result.status,'BLOCKED')
    def test_missing_and_empty_are_distinct_failures(self):
        a=self.failed('PERF_LIMITS_MISSING');b=self.failed('PERF_LIMITS_EMPTY',b'')
        self.assertNotEqual(a['failure'],b['failure'])
