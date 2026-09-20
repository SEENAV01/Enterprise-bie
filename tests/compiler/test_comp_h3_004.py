from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
import json,os,tempfile,unittest
from bie.compiler.host_toolchain import *
from bie.compiler.isolated_typesetting import *
from bie.compiler.equation_typesetting import typeset_latex

class IsolatedMathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.host=collect_host_toolchain()
    def test_content_identity_stable(self):self.assertEqual(self.host,collect_host_toolchain())
    def test_identity_digest_validated(self):self.assertEqual(validate_host_identity(self.host),self.host['identity_sha256'])
    def test_corrupt_identity_rejected(self):
        r=deepcopy(self.host);r['versions']['matplotlib']='invented'
        with self.assertRaisesRegex(ValueError,'TAMPERED'):validate_host_identity(r)
    def test_backend_and_font_bytes_have_hashes(self):
        self.assertTrue(any(p.endswith('.ttf') for p in self.host['files']));self.assertTrue(any('.so' in p for p in self.host['files']))
    def test_interpreter_and_compiler_bound(self):
        self.assertEqual(len(self.host['binaries']['python']),64);self.assertIn('bie.compiler/isolated_math_worker.py',self.host['files'])
    def test_identity_does_not_serialize_absolute_paths(self):
        text=json.dumps(self.host);self.assertNotIn('/mnt/data',text);self.assertNotIn('/opt/pyvenv',text)
    def test_no_font_distribution_or_whole_os_claim(self):
        self.assertFalse(self.host['font_bytes_distributed']);self.assertIn('whole_os_kernel',self.host['excluded'])
    def test_file_cache_detects_changed_bytes_even_preserved_mtime(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x';p.write_bytes(b'ab');st=p.stat();a=file_identity(p);p.write_bytes(b'cd');os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns));self.assertNotEqual(a,file_identity(p))
    def test_worker_geometry_matches_governed_backend(self):
        r=run_math_worker(r'\frac{x^2+1}{\sqrt{y}}','iso',32,self.host['identity_sha256']);self.assertEqual(r['geometry'],typeset_latex(r'\frac{x^2+1}{\sqrt{y}}',element_id='iso'))
    def test_worker_reports_applied_limits(self):
        r=run_math_worker('x','limits',32,self.host['identity_sha256']);self.assertEqual(r['observed_limits']['RLIMIT_CPU'],[15,15]);self.assertEqual(r['observed_limits']['RLIMIT_CORE'],[0,0]);self.assertFalse(r['os_security_sandbox'])
    def test_worker_rejects_stale_host(self):
        with self.assertRaisesRegex(ValueError,'HOST_MISMATCH'):run_math_worker('x','iso',32,'0'*64)
    def test_worker_is_not_parent_global_rc_state(self):
        import matplotlib as mpl
        with mpl.rc_context({'mathtext.fontset':'cm','text.usetex':True}):r=run_math_worker('x','rc',32,self.host['identity_sha256'])
        self.assertEqual(r['geometry'],typeset_latex('x',element_id='rc'))
    def test_parent_environment_not_forwarded(self):
        with patch.dict(os.environ,{'MPLCONFIGDIR':'/does/not/exist','OPENAI_API_KEY':'never-forward-this','LC_ALL':'invalid_LOCALE'}):
            r=run_math_worker('x','env',32,self.host['identity_sha256'])
        self.assertEqual(r['controlled_environment'],CONTROLS);self.assertNotIn('never-forward-this',json.dumps(r))
    def test_actual_timeout_is_failure(self):
        with self.assertRaisesRegex(ValueError,'TIMEOUT'):run_math_worker('x','deadline',32,self.host['identity_sha256'],limits=MathWorkerLimits(timeout_seconds=.001))
    def test_unsupported_latex_failure_not_plain_fallback(self):
        with self.assertRaisesRegex(ValueError,'LATEX_UNSUPPORTED'):run_math_worker(r'\unknown{x}','bad',32,self.host['identity_sha256'])
    def test_external_latex_command_rejected(self):
        with self.assertRaisesRegex(ValueError,'LATEX_UNSAFE'):run_math_worker(r'\input{anything}','bad',32,self.host['identity_sha256'])
    def test_input_budget_rejected(self):
        with self.assertRaisesRegex(ValueError,'INPUT_LIMIT'):run_math_worker('x'*2049,'large',32,self.host['identity_sha256'])
    def test_output_resource_limit_enforced(self):
        with self.assertRaises(ValueError):run_math_worker(r'\frac{x^2+1}{\sqrt{y}}','outbudget',32,self.host['identity_sha256'],limits=MathWorkerLimits(max_output_bytes=1024))
    def test_invalid_wall_limit_rejected(self):
        with self.assertRaises(ValueError):MathWorkerLimits(timeout_seconds=float('nan'))
    def test_boolean_cpu_limit_rejected(self):
        with self.assertRaises(ValueError):MathWorkerLimits(cpu_seconds=True)
    def test_invalid_memory_limit_rejected(self):
        with self.assertRaises(ValueError):MathWorkerLimits(memory_mb=10)
    def test_cache_returns_independent_geometry(self):
        a=isolated_typeset_latex('x+1',element_id='cache',expected_host=self.host);a['tree']['attrs']['tampered']=True;b=isolated_typeset_latex('x+1',element_id='cache',expected_host=self.host);self.assertNotIn('tampered',b['tree']['attrs'])
    def test_cache_rejects_different_declared_host(self):
        h=deepcopy(self.host);h.pop('identity_sha256');h['versions']['numpy']='other';h['identity_sha256']=digest(h)
        with self.assertRaisesRegex(ValueError,'MATH_HOST_CHANGED'):isolated_typeset_latex('x',element_id='host',expected_host=h)
    def test_parallel_real_workers_match(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs=[pool.submit(run_math_worker,'x^2','parallel',32,self.host['identity_sha256']) for _ in range(2)];a,b=[j.result() for j in jobs]
        self.assertEqual(a['geometry'],b['geometry'])
    def test_receipt_distinguishes_resource_isolation_from_sandbox(self):
        r=run_math_worker('x','scope',32,self.host['identity_sha256']);self.assertTrue(r['process_isolation']);self.assertFalse(r['os_security_sandbox']);self.assertFalse(r['accepted'])
if __name__=='__main__':unittest.main()
