import unittest,tempfile,sys,json,os,threading
from pathlib import Path
from bie.compiler.linux_worker import run_isolated,WorkerPolicy,worker_slot

class OperationalWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name);(self.p/'out').mkdir();self.locks=self.p/'locks';self.policy=WorkerPolicy(procfs=False)
    def tearDown(self):self.tmp.cleanup()
    def run_code(self,code,**kw):return run_isolated([sys.executable,'-c',code],workspace=self.p,writable=['out'],policy=kw.pop('policy',self.policy),lock_root=self.locks,**kw)
    def test_private_mount_pid_user_network_enforced(self):
        r,e=self.run_code('import os;print(os.getpid())');self.assertTrue(r.process.passed,r.process.stderr);self.assertEqual(r.process.stdout.strip(),'1');self.assertTrue(e['kernel_enforced']);self.assertTrue(e['capabilities_dropped'])
    def test_no_host_home_or_data(self):
        r,e=self.run_code('import os;print(os.path.exists("/mnt/data"),os.path.exists("/home/oai"))');self.assertEqual(r.process.stdout.strip(),'False False')
    def test_work_read_only(self):
        r,e=self.run_code('open("forbidden","w").write("bad")');self.assertFalse(r.process.passed);self.assertFalse((self.p/'forbidden').exists())
    def test_declared_output_writable(self):
        r,e=self.run_code('open("out/ok","w").write("verified")');self.assertTrue(r.process.passed,r.process.stderr);self.assertEqual((self.p/'out/ok').read_text(),'verified')
    def test_external_network_unreachable(self):
        r,e=self.run_code('import socket;s=socket.socket();s.settimeout(.2);s.connect(("1.1.1.1",80))');self.assertFalse(r.process.passed);self.assertIn('Network is unreachable',r.process.stderr)
    def test_loopback_available(self):
        r,e=self.run_code('import socket;s=socket.socket();s.bind(("127.0.0.1",0));print("OK")');self.assertTrue(r.process.passed,r.process.stderr)
    def test_chroot_syscall_denied(self):
        r,e=self.run_code('import os;os.chroot("/work")');self.assertFalse(r.process.passed);self.assertIn('Operation not permitted',r.process.stderr)
    def test_mount_capability_absent(self):
        r,e=self.run_code('import subprocess;raise SystemExit(subprocess.call(["/bin/mount","-t","tmpfs","tmpfs","/tmp"]))');self.assertFalse(r.process.passed)
    def test_timeout_kills_job(self):
        r,e=self.run_code('while True:pass',timeout_s=1);self.assertEqual(r.outcome,'TIMED_OUT')
    def test_output_limit_enforced(self):
        r,e=self.run_code('print("x"*1000000)',max_output_bytes=1000);self.assertEqual(r.outcome,'OUTPUT_LIMIT')
    def test_file_size_limit_enforced(self):
        r,e=self.run_code('open("out/large","wb").write(b"x"*100000)',policy=WorkerPolicy(procfs=False,file_bytes=2048));self.assertFalse(r.process.passed);self.assertLessEqual((self.p/'out/large').stat().st_size,2048)
    def test_environment_secrets_absent(self):
        os.environ['BIE_H7_TEST_SECRET']='not-for-child'
        try:r,e=self.run_code('import os;print(os.getenv("BIE_H7_TEST_SECRET"))');self.assertEqual(r.process.stdout.strip(),'None')
        finally:os.environ.pop('BIE_H7_TEST_SECRET',None)
    def test_fixed_concurrency_no_extra_job(self):
        p=WorkerPolicy(concurrent_jobs=1,procfs=False)
        with worker_slot(self.locks,p):
            with self.assertRaisesRegex(ValueError,'CONCURRENCY_LIMIT'):
                with worker_slot(self.locks,p):pass
    def test_slot_released_on_exception(self):
        p=WorkerPolicy(concurrent_jobs=1,procfs=False)
        try:
            with worker_slot(self.locks,p):raise RuntimeError('test')
        except RuntimeError:pass
        with worker_slot(self.locks,p):pass
    def test_slot_policy_drift_block(self):
        with worker_slot(self.locks,WorkerPolicy(concurrent_jobs=1,procfs=False)):pass
        with self.assertRaisesRegex(ValueError,'POLICY_MISMATCH'):
            with worker_slot(self.locks,self.policy):pass
    def test_symlink_output_block(self):
        (self.p/'link').symlink_to('/tmp',target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'PATH_INVALID'):run_isolated([sys.executable,'-c','print(1)'],workspace=self.p,writable=['link'],policy=self.policy,lock_root=self.locks)
    def test_invalid_policy(self):
        with self.assertRaisesRegex(ValueError,'POLICY_INVALID'):WorkerPolicy(concurrent_jobs=True)
    def test_private_proc_profile_never_silently_falls_back(self):
        r,e=self.run_code('print("PROC_OK")',policy=WorkerPolicy(procfs=True))
        if r.process.passed:self.assertTrue(e['private_procfs'])
        else:self.assertFalse(e['kernel_enforced']);self.assertIn('mount',r.process.stderr)

class OperationalMathAdoptionTests(unittest.TestCase):
    def test_actual_kernel_math(self):
        from bie.compiler.operational_math import run_operational_math
        from bie.compiler.host_toolchain import collect_host_toolchain
        r=run_operational_math('x^2','test',32,collect_host_toolchain()['identity_sha256']);self.assertTrue(r['os_security_sandbox']);self.assertTrue(r['kernel_policy']['private_network']);self.assertFalse(r['accepted'])
    def test_wrong_host_blocks_before_geometry(self):
        from bie.compiler.operational_math import run_operational_math
        self.assertRaises(ValueError,run_operational_math,'x','test',32,'0'*64)
    def test_input_bound(self):
        from bie.compiler.operational_math import run_operational_math
        self.assertRaises(ValueError,run_operational_math,'x'*2049,'test',32,'0'*64)
    def test_existing_compiler_uses_kernel_adapter(self):
        from bie.compiler.hardened_scene_compile import isolated_typeset_latex
        from bie.compiler.operational_math import operational_typeset_latex
        self.assertIs(isolated_typeset_latex,operational_typeset_latex)
