"""CLI and portable evidence checks; these do not authorize release."""
import contextlib,hashlib,io,json,os,tempfile,unittest
from pathlib import Path
from dataclasses import asdict
from unittest.mock import patch
from native_qa_support import inputs,positive,NOW,LIMITS
from bie.evaluation.benchmarks.models import canonical_json,digest,BenchmarkError
from bie.evaluation.benchmarks.native_qa import __main__ as cli
from bie.qa.release_v2.contracts import EvidenceBundle
from bie.qa.release_v2.codec import dumps
from bie.qa.release_v2.policy import enterprise_policy

class NativeQACLI001(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)
        self.art=self.root/'art';self.c,self.checks=inputs(self.art)
        (self.root/'bundle.json').write_bytes(dumps(EvidenceBundle('2.0.0',self.c,())))
        (self.root/'checks.json').write_text(canonical_json(self.checks))
        (self.root/'limits.json').write_text(canonical_json(asdict(LIMITS)))
        self.out=self.root/'output'
    def argv(self):
        values={'candidate-bundle':self.root/'bundle.json','checks':self.root/'checks.json',
          'limits':self.root/'limits.json','artifact-root':self.art,'as-of':NOW,
          'expected-candidate-digest':self.c.content_digest,'expected-policy-digest':enterprise_policy().content_digest,
          'expected-checks-digest':digest(self.checks),'output-dir':self.out}
        return [x for k,v in values.items() for x in ('--'+k,str(v))]
    def call(self):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):return cli.main(self.argv())
    def test_cli_executes_real_components_and_returns_blocked_exit(self):
        self.assertEqual(self.call(),2);r=json.loads((self.out/'RESULT.json').read_text())
        self.assertTrue(r['native_component_consumer_executed']);self.assertEqual(set(r['measurement_outcomes'].values()),{'PASS'})
        self.assertEqual(r['native_qa_report']['release_status'],'BLOCKED')
    def test_persistence_manifest_binds_exact_bytes(self):
        self.out.mkdir();m=cli.persist(self.out,positive())
        self.assertEqual(len(m),4)
        for n,row in m.items():
            raw=(self.out/n).read_bytes();self.assertEqual(len(raw),row['size_bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
    def test_report_export_rejects_wrong_hash(self):
        self.out.mkdir();r=positive();r['report_sha256']='0'*64
        with self.assertRaises(BenchmarkError):cli.persist(self.out,r)
    def test_existing_attempt_not_overwritten(self):
        self.out.mkdir();(self.out/'sentinel').write_text('keep');self.assertEqual(self.call(),2)
        self.assertEqual([p.name for p in self.out.iterdir()],['sentinel'])
    def test_symlink_output_rejected(self):
        target=self.root/'target';target.mkdir();self.out.symlink_to(target,target_is_directory=True)
        self.assertEqual(self.call(),2);self.assertEqual(list(target.iterdir()),[])
    def test_invalid_candidate_json_produces_blocked_receipt(self):
        (self.root/'bundle.json').write_text('{}');self.assertEqual(self.call(),2)
        self.assertFalse(json.loads((self.out/'RESULT.json').read_text())['native_component_consumer_executed'])
    def test_incomplete_operator_limits_blocked(self):
        (self.root/'limits.json').write_text('{}');self.assertEqual(self.call(),2)
        self.assertEqual(json.loads((self.out/'RESULT.json').read_text())['error_code'],'NATIVE_QA_EXPLICIT_LIMITS_REQUIRED')
    def test_bounded_reader_rejects_symlink(self):
        p=self.root/'link';p.symlink_to('bundle.json')
        with self.assertRaises(OSError):cli.read_bounded(p,4*1024**2)
    def test_bounded_reader_rejects_hardlink(self):
        p=self.root/'link';os.link(self.root/'bundle.json',p)
        with self.assertRaises(BenchmarkError):cli.read_bounded(p,4*1024**2)
    def test_bounded_reader_rejects_size(self):
        with self.assertRaises(BenchmarkError):cli.read_bounded(self.root/'bundle.json',1)
    def test_unexpected_execution_exception_not_success(self):
        with patch.object(cli,'execute',side_effect=RuntimeError('fixture exception')):self.assertEqual(self.call(),2)
        r=json.loads((self.out/'RESULT.json').read_text());self.assertEqual(r['status'],'BLOCKED');self.assertFalse(r['release_authorized'])
    def test_duplicate_json_keys_rejected(self):
        (self.root/'checks.json').write_text('{"a":1,"a":2}')
        self.assertEqual(self.call(),2);self.assertFalse(json.loads((self.out/'RESULT.json').read_text())['native_component_consumer_executed'])
    def test_native_report_export_uses_native_wire_serialization(self):
        r=positive();text=canonical_json(r)
        self.assertEqual(json.loads(text),r)
        self.assertIs(type(r['native_qa_report']['gate_results']),list)
