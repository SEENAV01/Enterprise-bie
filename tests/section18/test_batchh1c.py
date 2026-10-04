"""H1-003: real source process bounds and durable cancellation fault cuts.

All payloads are synthetic. Fault controls are not live-book acceptance.
Canonical parser, persistence and queue sources remain unchanged.
"""
from pathlib import Path
from dataclasses import replace
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
from test_batch001 import Base, DATA
from apps.operator.service import Service
from apps.operator.pdf_validation import inspect_source
from apps.operator.process_limits import PdfProcessBudget
from apps.operator.process_supervision import supervise, child_environment, ChildOutcome
from apps.operator.worker_execution import execute_worker
from apps.operator.contracts import OperatorError, Principal, PERMISSIONS
from bie.infrastructure.persistence import SQLitePersistence
from bie.infrastructure.durable_task_queue import SQLiteDurableTaskQueue


class ProcessBounds(Base):
    def test_real_canonical_parser_inside_os_bounded_child(self):
        result=inspect_source(DATA)
        self.assertEqual(result['status'],'VALID');self.assertGreater(result['page_count'],0)
        self.assertNotIn('title',result);self.assertNotIn('body',result)
    def test_invalid_pdf_is_invalid_not_fake_valid(self):
        self.assertEqual(inspect_source(b'private malformed bytes')['status'],'INVALID')
    def test_process_failure_is_blocked_not_invalid(self):
        self.assertEqual(inspect_source(DATA, PdfProcessBudget(memory_bytes=1024))['status'],'BLOCKED')
    def test_blocked_source_not_persisted_or_ready(self):
        blocked=dict(status='BLOCKED',diagnostic_codes=['pdf_resource_or_worker_failed'],
                     page_count=None,native_text_pages=None)
        with patch('apps.operator.service.inspect_source',return_value=blocked):source=self.source()
        self.assertFalse(source['stored']);self.assertEqual(source['validation']['status'],'BLOCKED')
        self.assertEqual(list((self.root/'sources-cas/blobs/sha256').glob('*/*')),[])
        self.error(lambda:self.service.create(self.p,source['source_id'],{},'blocked'),'source_not_valid')
    def test_no_provider_credentials_in_child_environment(self):
        import apps.operator.pdf_validation as module
        original=module.subprocess.Popen; seen=[]
        def start(*args,**kwargs):seen.append(kwargs['env']);return original(*args,**kwargs)
        with patch.dict(os.environ,{'OPENAI_API_KEY':'synthetic-secret-not-actual','BIE_OPERATOR_TOKEN':'synthetic-token-not-actual'}):
            with patch.object(module.subprocess,'Popen',side_effect=start):result=inspect_source(DATA)
        self.assertEqual(result['status'],'VALID');self.assertNotIn('OPENAI_API_KEY',seen[0]);self.assertNotIn('BIE_OPERATOR_TOKEN',seen[0])
    def test_invalid_process_limits_reject_booleans_and_widening(self):
        for options in ({'memory_bytes':True},{'memory_bytes':2*1024**3},{'cpu_seconds':31},
                        {'wall_seconds':46},{'cpu_seconds':0}):
            with self.subTest(options=options):
                with self.assertRaises(ValueError):PdfProcessBudget(**options)
    def test_input_size_checked_before_process_launch(self):
        with patch('apps.operator.pdf_validation.subprocess.Popen') as child:
            self.error(lambda:inspect_source(b''),'invalid_source_size')
        child.assert_not_called()
    def test_no_new_source_file_persistence_from_validation(self):
        before=set(self.root.rglob('*'));inspect_source(DATA)
        self.assertEqual(set(self.root.rglob('*')),before)
    def test_real_os_memory_limit_denies_large_allocation(self):
        root=Path(__file__).resolve().parents[2]
        code="import sys;sys.path.insert(0,sys.argv[1]);from apps.operator.process_limits import *;print(enforce_current_process(PdfProcessBudget()),flush=True)\ntry: data=bytearray(2*1024**3)\nexcept MemoryError: print('MEMORY_DENIED',flush=True)\nelse: raise SystemExit('BUDGET_BYPASSED')"
        result=subprocess.run([sys.executable,'-I','-B','-c',code,str(root)],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('MEMORY_DENIED',result.stdout)
        self.assertIn('WINDOWS_JOB_OBJECT' if os.name=='nt' else 'LINUX_RLIMIT',result.stdout)


class CancelRecovery(Base):
    def interrupt(self,method):
        run=self.make_run();kind=SQLiteDurableTaskQueue if method=='dead_letter' else SQLitePersistence
        original=getattr(kind,method); cut=[]
        def seeded(instance,*args,**kwargs):
            value=original(instance,*args,**kwargs)
            if not cut:cut.append(True);raise RuntimeError('seeded-crash-private-detail')
            return value
        with patch.object(kind,method,seeded):
            with self.assertRaises(RuntimeError):self.service.control(self.p,run,'cancel',1)
        return run
    def completed(self,run):
        result=Service(self.root,self.creds).control(self.p,run,'cancel',1)
        self.assertEqual(result['status'],'CANCELLED')
        self.assertEqual(self.service.status(self.p,run)['queue_state'],'DEAD_LETTER')
        with self.service.catalog.tx(read_only=True) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM audit_reservations').fetchone()[0],0)
            rows=[json.loads(r[0]) for r in db.execute('SELECT body FROM control_operations')]
            self.assertEqual(len(rows),1);self.assertEqual(rows[0]['state'],'COMPLETED')
            _,body=self.service.catalog.intent(db,self.p,run)
        with self.service.native(body) as native:
            events=native.persistence.load_run_state(body['native_job_id'])['events']
            self.assertEqual(sum(e['reason']=='operator_cancelled' for e in events),1)
    def test_queue_kill_crash_replayed_after_restart(self):self.completed(self.interrupt('dead_letter'))
    def test_attempt_save_crash_replayed_after_restart(self):self.completed(self.interrupt('save_attempt'))
    def test_transition_append_crash_replayed_after_restart(self):self.completed(self.interrupt('append_event'))
    def test_run_state_save_crash_replayed_after_restart(self):self.completed(self.interrupt('set_run_state'))
    def test_pending_cancel_read_never_claims_cancelled(self):
        run=self.interrupt('dead_letter');self.error(lambda:self.service.status(self.p,run),'control_reconciliation_required')
        response=self.get('runs/'+run);self.assertEqual(response.status_code,409)
        self.assertNotIn('seeded-crash-private-detail',response.text)
    def test_pending_cancel_prevents_native_dispatch(self):
        run=self.interrupt('dead_letter')
        with patch('apps.api.job_service.PdfInspectionJobService.run_once') as native:
            self.error(lambda:self.service.work_once(self.p,run),'control_reconciliation_required')
        native.assert_not_called()
    def test_pending_cancel_does_not_allow_resume(self):
        run=self.interrupt('dead_letter');self.error(lambda:self.service.control(self.p,run,'resume',1),'control_reconciliation_required')
    def test_wrong_revision_does_not_reconcile(self):
        run=self.interrupt('dead_letter');self.error(lambda:self.service.control(self.p,run,'cancel',2),'stale_revision')
    def test_foreign_tenant_cannot_reconcile(self):
        import time,secrets
        run=self.interrupt('dead_letter');foreign=Principal('foreign','other-tenant',PERMISSIONS,time.time()+3600)
        self.creds.grant(secrets.token_hex(32),foreign)
        self.error(lambda:self.service.control(foreign,run,'cancel',1),'run_not_found')
    def test_revoked_actor_cannot_reconcile(self):
        run=self.interrupt('dead_letter');self.creds.revoke(self.token)
        self.error(lambda:self.service.control(self.p,run,'cancel',1),'unauthorized')
    def test_pending_intent_tamper_detected(self):
        run=self.interrupt('dead_letter')
        with sqlite3.connect(self.service.catalog.path) as db:db.execute("UPDATE control_operations SET body='{}'")
        self.error(lambda:self.service.control(self.p,run,'cancel',1),'catalog_state_tampered')
    def test_different_queue_failure_is_not_fabricated_cancel(self):
        run=self.interrupt('dead_letter')
        with self.service.catalog.tx(read_only=True) as db:_,body=self.service.catalog.intent(db,self.p,run)
        with self.service.native(body) as native:native.queue.dead_letter('inspect-'+body['native_job_id'][4:],'different failure')
        self.error(lambda:self.service.control(self.p,run,'cancel',1),'cancel_queue_state_invalid')
    def test_terminal_replay_does_not_duplicate_receipts(self):
        run=self.make_run();self.service.control(self.p,run,'cancel',1)
        before=self.service.governance.audit(self.p)
        self.assertTrue(self.service.control(self.p,run,'cancel',1)['replayed'])
        self.assertEqual(self.service.governance.audit(self.p),before)
    def test_overlapping_cancel_coalesces_without_duplicate_receipts(self):
        run=self.make_run();entered=threading.Event();release=threading.Event()
        original=self.service._complete_cancel
        def held(*args):entered.set();self.assertTrue(release.wait(5));return original(*args)
        with patch.object(self.service,'_complete_cancel',side_effect=held):
            with ThreadPoolExecutor(max_workers=2) as pool:
                owner=pool.submit(self.service.control,self.p,run,'cancel',1)
                self.assertTrue(entered.wait(5))
                follower=pool.submit(self.service.control,self.p,run,'cancel',1)
                release.set();answers=[owner.result(10),follower.result(10)]
        self.assertTrue(all(a['status']=='CANCELLED' for a in answers));self.completed(run)
    def test_completed_cross_process_window_requires_exact_native_proof(self):
        run=self.make_run();original=self.service._complete_cancel
        def race(*args):original(*args);return original(*args)
        with patch.object(self.service,'_complete_cancel',side_effect=race):
            result=self.service.control(self.p,run,'cancel',1)
        self.assertTrue(result['replayed']);self.completed(run)
    def test_actual_two_process_cancel_returns_same_completed_state(self):
        run=self.make_run();root=Path(__file__).resolve().parents[2]
        # Explicit test-only barrier makes both processes prepare before either
        # completes. It cannot bypass production authorization or native proof.
        code="""import json,os,sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from apps.operator.service import Service
from apps.operator.contracts import Credentials,Principal,PERMISSIONS
class Racing(Service):
 def _complete_cancel(self,*args):
  marker=self.root/('test-barrier-'+sys.argv[4]);marker.write_bytes(b'')
  end=time.monotonic()+8
  while len(list(self.root.glob('test-barrier-*')))<2:
   if time.monotonic()>end:raise RuntimeError('test barrier timeout')
   time.sleep(.01)
  return super()._complete_cancel(*args)
c=Credentials();p=Principal('test-operator','tenant-a',PERMISSIONS,time.time()+60)
c.grant(os.environ['S18_TEST_TOKEN'],p)
print(json.dumps(Racing(Path(sys.argv[2]),c).control(p,sys.argv[3],'cancel',1)))
"""
        env=child_environment();env['S18_TEST_TOKEN']=self.token
        children=[subprocess.Popen([sys.executable,'-I','-B','-c',code,str(root),str(self.root),run,str(i)],
                                   stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env) for i in range(2)]
        try:
            results=[c.communicate(timeout=15) for c in children]
            self.assertEqual([c.returncode for c in children],[0,0],results)
            self.assertTrue(all(json.loads(out)['status']=='CANCELLED' for out,_ in results));self.completed(run)
        finally:
            for child in children:
                if child.poll() is None:child.kill();child.wait(timeout=5)
                child.stdout.close();child.stderr.close()


class WorkerProcessBoundary(Base):
    def test_actual_bounded_worker_executes_canonical_job(self):
        local=Principal('local-operator','local',PERMISSIONS,time.time()+60)
        self.creds.grant(self.token,local)
        source=self.service.import_pdf(local,DATA)
        run=self.service.create(local,source['source_id'],{},'bounded-worker')['run_id']
        with patch.dict(os.environ,{'BIE_OPERATOR_TOKEN':self.token}):result=execute_worker(self.root,run)
        self.assertEqual(result['outcome'],'ACKED');self.assertTrue(result['dispatched'])
        self.assertEqual(Service(self.root,self.creds).status(local,run)['status'],'SUCCEEDED')
    def test_independent_parent_wall_timeout_stops_sleeping_child(self):
        start=time.monotonic()
        result=supervise([sys.executable,'-I','-B','-c','import time;time.sleep(10)'],
                         child_environment(),PdfProcessBudget(wall_seconds=1))
        self.assertFalse(result.completed);self.assertLess(time.monotonic()-start,7)
    def test_child_output_overflow_is_bounded_and_not_success(self):
        result=supervise([sys.executable,'-I','-B','-c','print("x"*8192,flush=True)'],
                         child_environment(),PdfProcessBudget())
        self.assertFalse(result.completed);self.assertLessEqual(len(result.output),4096)
    def test_unavailable_process_does_not_fake_success(self):
        result=supervise([str(self.root/'missing-executable')],child_environment(),PdfProcessBudget())
        self.assertFalse(result.completed)
    def test_worker_child_contract_does_not_echo_internal_detail(self):
        outcome=ChildOutcome(0,b'{"enforcement":"LINUX_RLIMIT","result":{"traceback":"private-detail"}}',True)
        with patch('apps.operator.worker_execution.supervise',return_value=outcome):
            self.error(lambda:execute_worker(self.root,'valid-run'),'worker_contract_invalid')
    def test_worker_only_receives_its_required_credential(self):
        calls=[]
        def child(command,env,budget):calls.append(env);return ChildOutcome(2,b'',False)
        with patch.dict(os.environ,{'BIE_OPERATOR_TOKEN':self.token,'OPENAI_API_KEY':'not-actual-secret'}):
            with patch('apps.operator.worker_execution.supervise',side_effect=child):
                self.error(lambda:execute_worker(self.root,'valid-run'),'worker_process_failed')
        self.assertEqual(calls[0]['BIE_OPERATOR_TOKEN'],self.token);self.assertNotIn('OPENAI_API_KEY',calls[0])


TASK_CLASSES={'BIE-APP-H1-003':(ProcessBounds,CancelRecovery,WorkerProcessBoundary)}


def selected_suite(task=None):
    suite=unittest.TestSuite()
    for classes in TASK_CLASSES.values() if task is None else (TASK_CLASSES[task],):
        for cls in classes:suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    return suite


if __name__=='__main__':unittest.main(verbosity=2)
