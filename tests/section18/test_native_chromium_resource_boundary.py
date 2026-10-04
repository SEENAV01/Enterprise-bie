"""H1-008 genuine Linux cgroup/PID controls; no fallback or skipped gates."""
from pathlib import Path
from dataclasses import asdict
import json,os,resource,signal,subprocess,sys,tempfile,time,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from bie.compiler import chromium_resource_worker as boundary
from bie.compiler.qa_common import CompilerQAError
from bie.compiler.linux_worker import WorkerPolicy,run_isolated
NODE='/opt/nvm/versions/node/v22.16.0/bin/node';MIB=1024**2

class NativeChromiumResources(unittest.TestCase):
    records=[]
    @classmethod
    def setUpClass(cls):
        if sys.platform!='linux' or os.getuid()!=0:raise RuntimeError('explicit root Linux supervisor required')
        cls.project=Path(os.environ['BIE_SECTION18_RENDER_PROJECT'])
    def wait_stop(self,p):
        end=time.monotonic()+5
        while not boundary.stopped(p.pid):
            self.assertIsNone(p.poll());self.assertLess(time.monotonic(),end);time.sleep(.01)
    def memory(self,negative):
        group=boundary.OwnedMemoryGroup();child=None
        try:
            constructor=group.receipt();self.assertEqual(constructor['memory_max'],2*1024**3)
            # Test-only tightening to64MiB proves OOM with a small128MiB child.
            # Never use a dangerous2GiB allocation fixture or increase any cap.
            (group.path/'memory.max').write_text(str(64*MIB));size=128*MIB if negative else 8*MIB
            code=('import json,os,resource,signal;resource.setrlimit(resource.RLIMIT_AS,(8589934592,8589934592));'
                  'os.kill(os.getpid(),signal.SIGSTOP);data=bytearray('+str(size)+');'
                  'print(json.dumps(dict(bytes=len(data),limit=resource.getrlimit(resource.RLIMIT_AS))),flush=True)')
            child=subprocess.Popen([sys.executable,'-I','-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            self.wait_stop(child);group.join(child.pid);os.kill(child.pid,signal.SIGCONT)
            stdout,stderr=child.communicate(timeout=10);receipt=group.receipt()
            if negative:
                self.assertEqual(child.returncode,-signal.SIGKILL);self.assertGreaterEqual(receipt['memory_events']['oom_kill'],1)
                self.assertNotIn(b'"bytes"',stdout)
            else:
                self.assertEqual(child.returncode,0,stderr.decode());self.assertEqual(json.loads(stdout)['bytes'],8*MIB)
                self.assertEqual(json.loads(stdout)['limit'],[boundary.NODE_AS]*2)
                self.assertEqual(receipt['memory_events']['oom_kill'],0)
            self.records.append(dict(control='REAL_OOM_NEGATIVE' if negative else 'REAL_ALLOCATION_POSITIVE',
                original_constructor_policy=constructor,test_only_tightened_cap=64*MIB,exit_code=child.returncode,
                cgroup=receipt,synthetic_test=True,passed=True))
        finally:
            group.close()
            if child is not None:
                if child.poll() is None:child.kill()
                child.communicate(timeout=2)
            self.assertFalse(group.path.exists())
    def test_live_default_worker_policy_unchanged(self):
        self.assertEqual(asdict(WorkerPolicy()),dict(procfs=True,concurrent_jobs=2,cpu_seconds=120,
            address_space_bytes=8589934592,file_bytes=1073741824,descriptors=256,processes=128,tmpfs_bytes=536870912))
        self.assertEqual(subprocess.check_output([NODE,'--version'],text=True).strip(),'v22.16.0')
        self.records.append(dict(control='ORIGINAL_POLICY',policy=asdict(WorkerPolicy()),node='22.16.0',passed=True))
    def test_unrelated_genuine_node_remains_unflagged_eight_gib(self):
        code="const fs=require('fs');console.log(JSON.stringify({args:process.execArgv,options:process.env.NODE_OPTIONS||null,limit:fs.readFileSync('/proc/self/limits','utf8')}))"
        with tempfile.TemporaryDirectory(prefix='bie-native-generic-slots-') as locks:
            result,kernel=run_isolated([NODE,'-e',code],workspace=self.project,engine=ROOT,policy=WorkerPolicy(),
                timeout_s=10,max_output_bytes=65536,lock_root=locks)
        self.assertTrue(result.process.passed,result.process.stderr)
        value=json.loads(result.process.stdout);self.assertEqual(value['args'],['-e',code]);self.assertIsNone(value['options'])
        row=next(s for s in value['limit'].splitlines() if s.startswith('Max address space'))
        self.assertEqual(row.removeprefix('Max address space').split(),['8589934592','8589934592','bytes'])
        self.assertEqual(kernel['resource_limits'],asdict(WorkerPolicy()));self.assertTrue(kernel['kernel_enforced'])
        self.records.append(dict(control='GENERIC_NODE_NO_FLAG',kernel=kernel,passed=True))
    def test_production_physical_swap_pid_limits_exact_and_owned_cleanup(self):
        before=boundary.bounded_read(boundary.CGROOT/'cgroup.subtree_control');group=boundary.OwnedMemoryGroup()
        try:
            receipt=group.receipt();self.assertEqual(receipt['memory_max'],boundary.PHYSICAL_MEMORY)
            self.assertEqual(receipt['swap_max'],0);self.assertEqual(receipt['pids_max'],128)
            self.assertNotIn(os.getpid(),group.members());self.records.append(dict(control='EXACT_PRODUCTION_CGROUP',cgroup=receipt,passed=True))
        finally:group.close()
        self.assertFalse(group.path.exists());self.assertEqual(before,boundary.bounded_read(boundary.CGROOT/'cgroup.subtree_control'))
    def test_small_real_allocation_positive(self):self.memory(False)
    def test_small_real_oom_negative(self):self.memory(True)
    def test_foreign_host_pid_never_receives_grant(self):
        group=boundary.OwnedMemoryGroup();before=resource.getrlimit(resource.RLIMIT_AS)
        try:
            with self.assertRaisesRegex(CompilerQAError,'FOREIGN_PROCESS'):boundary._grant(group,os.getpid(),[], '', '', '')
            self.assertEqual(resource.getrlimit(resource.RLIMIT_AS),before)
            self.records.append(dict(control='FOREIGN_PID_DENIED',host_limit_unchanged=True,passed=True))
        finally:group.close()
    def test_stopped_owned_child_with_foreign_parent_never_receives_grant(self):
        group=boundary.OwnedMemoryGroup();child=None
        code='import os,resource,signal,time;resource.setrlimit(resource.RLIMIT_AS,(8589934592,8589934592));os.kill(os.getpid(),signal.SIGSTOP);time.sleep(10)'
        try:
            child=subprocess.Popen([sys.executable,'-I','-c',code],start_new_session=True)
            self.wait_stop(child);group.join(child.pid)
            with self.assertRaisesRegex(CompilerQAError,'FOREIGN_PROCESS'):boundary._grant(group,child.pid,[], '', '', '')
            self.assertEqual(resource.prlimit(child.pid,resource.RLIMIT_AS),(boundary.NODE_AS,)*2)
            self.records.append(dict(control='FORGED_ENTRY_PARENT_DENIED',child_as_limit=[boundary.NODE_AS]*2,passed=True))
        finally:
            group.close()
            if child is not None:
                if child.poll() is None:child.kill()
                child.wait(timeout=2)

if __name__=='__main__':unittest.main(verbosity=2)
