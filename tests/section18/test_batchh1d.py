"""Finding-derived H1-005: real bounded CAS admission and interruption controls."""
from pathlib import Path
from dataclasses import asdict
import hashlib,json,os,subprocess,sys,tempfile,time,unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from apps.operator.cas_budget import CASBudget,CASLimits,BudgetedCAS
from apps.operator.contracts import OperatorError,canonical
from bie.infrastructure.artifact_store import ArtifactStoreError
from test_campaign_sidecar_race import CampaignSidecarRace
from test_campaign_maintenance import CampaignMaintenance
from test_worker_recovery import WorkerRecovery
from test_catalog_file_race import CatalogFileSafety
from test_terminal_worker_recovery import TerminalWorkerRecovery
from test_failed_terminal_recovery import FailedTerminalRecovery
from test_quota_terminal_recovery import QuotaTerminalRecovery

CHILD='''from pathlib import Path
import json,os,sys,time
from apps.operator.cas_budget import CASBudget,BudgetedCAS
from apps.operator.contracts import OperatorError
root=Path(sys.argv[1]);mode=sys.argv[2];data=sys.argv[3].encode()
b=CASBudget(root);c=BudgetedCAS(root/'sources-cas',b)
if mode=='crash':
    import bie.infrastructure.artifact_store as native
    native.os.replace=lambda *args: os._exit(74)
    c.put_bytes(data)
elif mode=='lock':
    with b.lock():
        print('LOCKED',flush=True)
        time.sleep(2)
else:
    deadline=time.monotonic()+5
    while not (root/'release').exists():
        if time.monotonic()>deadline:raise SystemExit(73)
        time.sleep(.005)
    try:
        ref=c.put_bytes(data)
        print(json.dumps(dict(status='STORED',sha256=ref.digest)))
    except OperatorError as e:
        print(json.dumps(dict(status='REJECTED',code=e.code,http=e.status)))
'''

class CASCapacity(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='bie-s18-cas-budget-')
        self.root=Path(self.tmp.name)
        self.limits=CASLimits(max_bytes=8,max_files=2,max_blob_bytes=8)
        self.budget=CASBudget(self.root,self.limits)
        self.cas=BudgetedCAS(self.root/'sources-cas',self.budget)
    def tearDown(self):self.tmp.cleanup()
    def error(self,code,operation,status=None):
        with self.assertRaises(OperatorError) as caught:operation()
        self.assertEqual(caught.exception.code,code)
        if status is not None:self.assertEqual(caught.exception.status,status)
    def spawn(self,mode,data):
        env={k:v for k,v in os.environ.items() if k in ('PATH','SystemRoot','TEMP','TMP','WINDIR')}
        env.update(PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
        p=subprocess.Popen([sys.executable,'-B','-c',CHILD,str(self.root),mode,data],
                           cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        self.addCleanup(self.reap,p)
        return p
    @staticmethod
    def reap(p):
        if p.poll() is None:p.kill()
        p.wait(timeout=5)
        for stream in (p.stdout,p.stderr):stream.close()
    def test_exact_byte_boundary_is_admitted_and_verified(self):
        ref=self.cas.put_bytes(b'12345678')
        self.assertEqual(self.cas.get_bytes(ref),b'12345678')
        self.assertEqual(self.budget.inventory()['bytes'],8)
    def test_one_byte_over_aggregate_rejects_without_partial_blob(self):
        self.cas.put_bytes(b'1234567')
        before=self.budget.inventory()
        self.error('cas_capacity_reached',lambda:self.cas.put_bytes(b'xy'),429)
        self.assertEqual(self.budget.inventory(),before)
        self.assertFalse(self.cas._path(hashlib.sha256(b'xy').hexdigest()).exists())
    def test_duplicate_at_exact_capacity_does_not_add_bytes_or_files(self):
        a=self.cas.put_bytes(b'12345678');before=self.budget.inventory()
        self.assertEqual(self.cas.put_bytes(b'12345678'),a)
        self.assertEqual(self.budget.inventory(),before)
    def test_zero_byte_blob_still_consumes_one_file(self):
        self.cas.put_bytes(b'');self.cas.put_bytes(b'a')
        self.error('cas_capacity_reached',lambda:self.cas.put_bytes(b'b'),429)
        self.assertEqual(self.budget.inventory()['files'],2)
    def test_exact_file_boundary_and_read_at_capacity(self):
        a=self.cas.put_bytes(b'a');self.cas.put_bytes(b'b')
        self.assertEqual(self.cas.get_bytes(a),b'a')
        self.error('cas_capacity_reached',lambda:self.cas.put_bytes(b'c'),429)
    def test_restart_recovers_actual_usage_without_resetting_capacity(self):
        self.cas.put_bytes(b'12345678')
        restarted=CASBudget(self.root)
        self.assertEqual(restarted.limits,self.limits)
        self.error('cas_capacity_reached',lambda:BudgetedCAS(self.root/'sources-cas',restarted).put_bytes(b'a'),429)
    def test_conflicting_restart_policy_is_not_silently_accepted(self):
        self.error('cas_policy_conflict',lambda:CASBudget(self.root,CASLimits(max_bytes=9)))
        self.assertEqual(CASBudget(self.root).limits,self.limits)
    def test_policy_tampering_is_rejected_in_existing_process(self):
        self.budget.policy_path.write_bytes(canonical(asdict(CASLimits(max_bytes=9))))
        self.error('cas_policy_tampered',lambda:self.cas.put_bytes(b'a'))
        self.assertFalse(self.cas._path(hashlib.sha256(b'a').hexdigest()).exists())
    def test_limits_cannot_widen_governed_ceiling_or_accept_bool(self):
        for key,value in [('max_bytes',1024**3+1),('max_files',32769),('max_blob_bytes',256*1024**2+1),
                          ('max_inventory_entries',65537),('max_files',True),('max_bytes',0)]:
            self.error('cas_budget_invalid',lambda key=key,value=value:CASLimits(**{key:value}),400)
    def test_blob_limit_is_independent_of_aggregate_capacity(self):
        self.error('cas_blob_too_large',lambda:self.cas.put_bytes(b'123456789'),413)
        self.assertEqual(self.budget.inventory()['bytes'],0)
    def test_foreign_run_cas_bytes_cannot_bypass_root_capacity(self):
        other=BudgetedCAS(self.root/'runs'/'run-other'/'cas',self.budget)
        other.put_bytes(b'12345678')
        self.error('cas_capacity_reached',lambda:self.cas.put_bytes(b'a'),429)
        self.assertEqual(self.budget.inventory()['bytes'],8)
    def test_existing_native_blob_corruption_remains_rejected(self):
        ref=self.cas.put_bytes(b'abcd');self.cas._path(ref.digest).write_bytes(b'WXYZ')
        with self.assertRaises(ArtifactStoreError):self.cas.put_bytes(b'abcd')
        with self.assertRaises(ArtifactStoreError):self.cas.get_bytes(ref)
    def test_real_interrupted_native_write_is_charged_after_restart(self):
        p=self.spawn('crash','12345678');stdout,stderr=p.communicate(timeout=10)
        self.assertEqual(p.returncode,74,stderr);self.assertEqual(stdout,'')
        leftovers=list((self.root/'sources-cas').rglob('.cas-*'))
        self.assertEqual(len(leftovers),1);self.assertEqual(leftovers[0].read_bytes(),b'12345678')
        self.assertFalse(self.cas._path(hashlib.sha256(b'12345678').hexdigest()).exists())
        b=CASBudget(self.root);self.assertEqual(b.inventory()['bytes'],8)
        self.error('cas_capacity_reached',lambda:BudgetedCAS(self.root/'sources-cas',b).put_bytes(b'a'),429)
        self.assertTrue(leftovers[0].exists(),'No silent deletion of interrupted evidence')
    def test_two_actual_processes_cannot_overcommit_exact_capacity(self):
        a=self.spawn('write','12345678');b=self.spawn('write','abcdefgh')
        (self.root/'release').touch()
        rows=[]
        for p in (a,b):
            stdout,stderr=p.communicate(timeout=10);self.assertEqual(p.returncode,0,stderr);rows.append(json.loads(stdout))
        self.assertEqual(sorted(x['status'] for x in rows),['REJECTED','STORED'])
        denied=next(x for x in rows if x['status']=='REJECTED')
        self.assertEqual((denied['code'],denied['http']),('cas_capacity_reached',429))
        self.assertEqual(self.budget.inventory()['bytes'],8);self.assertEqual(self.budget.inventory()['files'],1)
    def test_two_actual_processes_same_content_deduplicate(self):
        a=self.spawn('write','12345678');b=self.spawn('write','12345678');(self.root/'release').touch()
        rows=[]
        for p in (a,b):
            stdout,stderr=p.communicate(timeout=10);self.assertEqual(p.returncode,0,stderr);rows.append(json.loads(stdout))
        self.assertEqual(rows[0],rows[1]);self.assertEqual(rows[0]['status'],'STORED')
        self.assertEqual(self.budget.inventory()['files'],1)
    def test_terminated_lock_owner_does_not_leave_false_reservation(self):
        p=self.spawn('lock','');self.assertEqual(p.stdout.readline().strip(),'LOCKED')
        p.terminate();p.wait(timeout=5)
        ref=self.cas.put_bytes(b'a');self.assertEqual(self.cas.get_bytes(ref),b'a')
    def test_no_unbounded_physical_inventory(self):
        limited=CASLimits(max_bytes=8,max_files=2,max_inventory_entries=1,max_blob_bytes=8)
        separate=self.root/'separate';separate.mkdir();b=CASBudget(separate,limited)
        c=BudgetedCAS(separate/'sources-cas',b)
        self.error('cas_inventory_capacity_reached',lambda:c.put_bytes(b'a'),503)
    def test_hardlinked_blob_cannot_be_admitted_as_safe_storage(self):
        ref=self.cas.put_bytes(b'abcd');os.link(self.cas._path(ref.digest),self.root/'second-link')
        self.error('storage_link_rejected',lambda:self.cas.put_bytes(b'x'))
    def test_budgeted_path_cannot_escape_owned_root(self):
        with self.assertRaises((OperatorError,ValueError)):
            BudgetedCAS(self.root.parent/'foreign-cas',self.budget)
    def test_hardlinked_policy_cannot_define_trusted_capacity(self):
        os.link(self.budget.policy_path,self.root/'policy-alias')
        self.error('cas_policy_invalid',lambda:CASBudget(self.root))
    def test_invalid_policy_returns_governed_error_not_parser_details(self):
        self.budget.policy_path.write_bytes(b'')
        self.error('cas_policy_invalid',lambda:CASBudget(self.root))
    def test_deep_inventory_is_bounded_without_recursion_overflow(self):
        nested=self.root/'sources-cas'
        for _ in range(17):nested=nested/'x'
        nested.mkdir(parents=True)
        self.error('cas_inventory_depth_reached',lambda:self.budget.inventory(),503)

TASK_CLASSES={'BIE-APP-H1-005':[CASCapacity,WorkerRecovery,CatalogFileSafety,TerminalWorkerRecovery,FailedTerminalRecovery,QuotaTerminalRecovery],'BIE-APP-H1-006':[CampaignSidecarRace,CampaignMaintenance]}
def selected_suite(task=None):
    suite=unittest.TestSuite()
    for name,classes in TASK_CLASSES.items():
        if task is None or task==name:
            for cls in classes:suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    return suite
if __name__=='__main__':unittest.main(verbosity=2)
