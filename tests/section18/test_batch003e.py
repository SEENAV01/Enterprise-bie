"""Finding-derived H1-001; real RUN001 race preserved, no timeout/assertion bypass."""
import threading,time,unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from test_batch001 import Base
from apps.operator.admission import CreationAdmission,for_root
from apps.operator.service import Service
from apps.operator.contracts import OperatorError

class AdmissionHardening(Base):
    def overlapping(self,fn,followers=1):
        entered=threading.Event();release=threading.Event()
        def owner():entered.set();self.assertTrue(release.wait(3));return fn()
        admission=CreationAdmission(wait_seconds=3)
        pool=ThreadPoolExecutor(max_workers=followers+1)
        first=pool.submit(admission.run,'same',owner);self.assertTrue(entered.wait(3))
        rest=[pool.submit(admission.run,'same',lambda:self.fail('duplicate operation')) for _ in range(followers)]
        deadline=time.monotonic()+3
        while admission._waiters<followers and time.monotonic()<deadline:time.sleep(.001)
        self.assertEqual(admission._waiters,followers)
        release.set();return admission,pool,first,rest

    def test_shared_root_coordinator_across_services(self):
        other=Service(self.root,self.creds)
        self.assertIs(self.service._creation_admission,other._creation_admission)
    def test_different_root_coordinators_do_not_share(self):
        self.assertIsNot(for_root(self.root),for_root(self.root/'other'))
    def test_one_owner_committed_result_for_overlapping_requests(self):
        a,pool,first,rest=self.overlapping(lambda:{'run_id':'real-committed'},2)
        with pool:
            self.assertEqual(first.result(),({'run_id':'real-committed'},False))
            self.assertTrue(all(x.result()==({'run_id':'real-committed'},True) for x in rest))
        self.assertEqual(a._flights,{});self.assertEqual(a._waiters,0)
    def test_no_historical_cache_after_completion(self):
        a=CreationAdmission();calls=[]
        for i in range(2):self.assertEqual(a.run('same',lambda:calls.append(i) or i),(i,False))
        self.assertEqual(calls,[0,1])
    def test_returned_results_are_not_shared_mutable_state(self):
        a,pool,first,rest=self.overlapping(lambda:{'safe':[]},2)
        with pool:
            values=[first.result()[0]]+[x.result()[0] for x in rest]
        values[0]['safe'].append('changed');self.assertEqual(values[1]['safe'],[]);self.assertEqual(values[2]['safe'],[])
    def test_governed_failure_fans_out_safe_code(self):
        def failed():raise OperatorError('source_not_valid',409)
        a,pool,first,rest=self.overlapping(failed)
        with pool:
            for x in [first]+rest:
                with self.assertRaises(OperatorError) as ctx:x.result()
                self.assertEqual((ctx.exception.code,ctx.exception.status),('source_not_valid',409))
        self.assertEqual(a._flights,{})
    def test_internal_failure_detail_not_shared_to_waiter(self):
        def failed():raise RuntimeError('SECRET_PRIVATE_PATH')
        a,pool,first,rest=self.overlapping(failed)
        with pool:
            with self.assertRaises(RuntimeError):first.result()
            with self.assertRaises(OperatorError) as ctx:rest[0].result()
            self.assertEqual((ctx.exception.code,ctx.exception.status),('internal_error',500))
            self.assertNotIn('SECRET',str(ctx.exception))
    def test_owner_capacity_exhaustion_does_not_execute(self):
        a=CreationAdmission(max_owners=1);entered=threading.Event();release=threading.Event()
        with ThreadPoolExecutor(max_workers=1) as pool:
            f=pool.submit(a.run,'busy',lambda:entered.set() or release.wait(3));self.assertTrue(entered.wait(3))
            try:self.error(lambda:a.run('other',lambda:self.fail('executed')),'creation_admission_full')
            finally:release.set();f.result()
    def test_waiter_capacity_exhaustion_is_bounded(self):
        a=CreationAdmission(max_waiters=1);entered=threading.Event();release=threading.Event()
        with ThreadPoolExecutor(max_workers=2) as pool:
            f=pool.submit(a.run,'same',lambda:entered.set() or release.wait(3));self.assertTrue(entered.wait(3))
            follower=pool.submit(a.run,'same',lambda:self.fail('executed'))
            deadline=time.monotonic()+3
            while a._waiters<1 and time.monotonic()<deadline:time.sleep(.001)
            try:self.error(lambda:a.run('same',lambda:self.fail('executed')),'creation_admission_full')
            finally:release.set();f.result();follower.result()
        self.assertEqual(a._waiters,0)
    def test_wait_timeout_never_cancels_owner_or_fakes_failure(self):
        a=CreationAdmission(wait_seconds=.03);entered=threading.Event();release=threading.Event()
        with ThreadPoolExecutor(max_workers=1) as pool:
            f=pool.submit(a.run,'same',lambda:entered.set() or release.wait(3) or 'result');self.assertTrue(entered.wait(3))
            try:self.error(lambda:a.run('same',lambda:self.fail('executed')),'creation_admission_timeout');self.assertFalse(f.done())
            finally:release.set();self.assertFalse(f.result()[1])
        self.assertEqual(a._waiters,0);self.assertEqual(a._flights,{})
    def test_failed_owner_releases_slot_for_recovery(self):
        a=CreationAdmission()
        self.error(lambda:a.run('same',lambda:(_ for _ in ()).throw(OperatorError('seeded_failure'))),'seeded_failure')
        self.assertEqual(a.run('same',lambda:'recovered'),('recovered',False))
    def test_actual_concurrent_creation_single_native_submission(self):
        source=self.source()['source_id'];other=Service(self.root,self.creds);entered=threading.Event();calls=[]
        original=self.service._create
        def slow(*args,**kwargs):calls.append(1);entered.set();time.sleep(1.25);return original(*args,**kwargs)
        with patch.object(self.service,'_create',side_effect=slow),ThreadPoolExecutor(max_workers=3) as pool:
            owner=pool.submit(self.service.create,self.p,source,{},'same');self.assertTrue(entered.wait(3))
            requests=[pool.submit(other.create,self.p,source,{},'same') for _ in range(2)]
            result=[owner.result()]+[x.result() for x in requests]
        self.assertEqual(len(calls),1);self.assertEqual(len({x['run_id'] for x in result}),1)
        self.assertEqual(sum(x['replayed'] for x in result),2)
        self.assertEqual(len(self.service.list_runs(self.p)['items']),1)
        self.assertEqual(self.service.work_once(self.p,result[0]['run_id'])['outcome'],'ACKED')
    def test_conflicting_config_does_not_share_success(self):
        source=self.source()['source_id'];self.service.create(self.p,source,{},'same')
        self.error(lambda:self.service.create(self.p,source,{'locale':'hi'},'same'),'idempotency_conflict')
    def test_revocation_while_waiting_prevents_result_disclosure(self):
        source=self.source()['source_id'];entered=threading.Event();release=threading.Event();original=self.service._create
        # The owner executes native creation before revocation; both response
        # paths still recheck the grant, so persisted work is not fake-cancelled.
        def committed(*args,**kwargs):
            value=original(*args,**kwargs);entered.set();self.assertTrue(release.wait(3));return value
        with patch.object(self.service,'_create',side_effect=committed),ThreadPoolExecutor(max_workers=2) as pool:
            owner=pool.submit(self.service.create,self.p,source,{},'same');self.assertTrue(entered.wait(5))
            follower=pool.submit(self.service.create,self.p,source,{},'same');a=self.service._creation_admission
            deadline=time.monotonic()+3
            while a._waiters<1 and time.monotonic()<deadline:time.sleep(.001)
            self.assertEqual(a._waiters,1);self.creds.revoke(self.token);release.set()
            for f in (owner,follower):
                with self.assertRaises(OperatorError) as ctx:f.result()
                self.assertEqual(ctx.exception.code,'unauthorized')
    def test_invalid_admission_limits_fail_closed(self):
        for args in ({'wait_seconds':float('nan')},{'wait_seconds':float('inf')},{'wait_seconds':True},{'max_owners':33},{'max_waiters':65}):
            with self.subTest(args=args):self.error(lambda:CreationAdmission(**args),'invalid_admission_limit')

TASK_CLASSES={'BIE-APP-H1-001':AdmissionHardening}
def selected_suite(task=None):
    suite=unittest.TestSuite()
    for key,cls in TASK_CLASSES.items():
        if task is None or task==key:
            for name in sorted(cls.__dict__):
                if name.startswith('test_'):suite.addTest(cls(name))
    return suite
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(selected_suite());raise SystemExit(not result.wasSuccessful())
