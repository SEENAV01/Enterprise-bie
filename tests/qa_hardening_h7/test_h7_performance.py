from h7_helpers import *
import subprocess,time

class Performance(Temp):
    def setUp(self):
        super().setUp();self.p=AggregateLimits();self.rows=[dict(job_id='a',execution_id='aa',submitted_ns=0,started_ns=1,finished_ns=11,exit_code=0,output_verified=True),dict(job_id='b',execution_id='bb',submitted_ns=0,started_ns=2,finished_ns=21,exit_code=0,output_verified=True)]
        self.cg=dict(kernel_cgroup2=True,memory_limit_bytes=self.p.memory_bytes,memory_peak_bytes=1024,raw={'memory.events':'low 0\nhigh 0\nmax 0\noom 0\noom_kill 0\n'})
    def call(self,rows=None,cg='default',p=None):
        return evaluate_workload(('a','b'),rows if rows is not None else self.rows,p or self.p,binding=self.binding(p or self.p),cgroup=self.cg if cg=='default' else cg)
    def codes(self,r):return [f['code'] for f in r['report']['findings']]
    def test_complete_accounting(self):
        r=self.call();self.assertEqual(r['details']['submitted'],2);self.assertEqual(r['details']['p95_latency_ns'],21);self.assertEqual(r['details']['verified_outputs'],2);self.assertFalse(r['production_authorized'])
    def test_memory_missing(self):self.assertIn('H7_AGGREGATE_MEASUREMENT_MISSING',self.codes(self.call(cg=None)))
    def test_memory_over(self):self.assertIn('H7_AGGREGATE_MEMORY_EXCEEDED',self.codes(self.call(cg={**self.cg,'memory_peak_bytes':self.p.memory_bytes+1})))
    def test_oom_blocks(self):self.assertIn('H7_AGGREGATE_OOM',self.codes(self.call(cg={**self.cg,'raw':{'memory.events':'oom 1\noom_kill 1'}})))
    def test_different_limit(self):self.error('H7_AGGREGATE_LIMIT_MISMATCH',self.call,cg={**self.cg,'memory_limit_bytes':1})
    def test_false_kernel(self):self.error('H7_AGGREGATE_NOT_KERNEL',self.call,cg={**self.cg,'kernel_cgroup2':False})
    def test_missing_events(self):self.error('H7_MEMORY_EVENTS_MISSING',self.call,cg={**self.cg,'raw':{'memory.events':''}})
    def test_negative_events(self):self.error('H7_MEMORY_EVENTS_MISSING',self.call,cg={**self.cg,'raw':{'memory.events':'oom -1\noom_kill 0'}})
    def test_corrupt_events(self):self.error('H7_MEMORY_EVENTS',self.call,cg={**self.cg,'raw':{'memory.events':'oom x'}})
    def test_missing_job(self):self.error('H7_JOB_CENSUS',self.call,self.rows[:-1])
    def test_duplicate_job(self):self.error('H7_JOB_CENSUS',self.call,self.rows+[self.rows[0]])
    def test_foreign_job(self):self.error('H7_JOB_CENSUS',self.call,[self.rows[0],{**self.rows[1],'job_id':'x'}])
    def test_replayed_execution(self):self.error('H7_PERF_REPLAY',self.call,[self.rows[0],{**self.rows[1],'execution_id':'aa'}])
    def test_bad_clock(self):self.error('H7_JOB_CLOCK_ORDER',self.call,[{**self.rows[0],'started_ns':20},self.rows[1]])
    def test_failed_job_retained(self):
        r=self.call([{**self.rows[0],'exit_code':1},self.rows[1]]);self.assertIn('H7_UNVERIFIED_JOB',self.codes(r));self.assertEqual(r['details']['submitted'],2);self.assertEqual(r['details']['verified_outputs'],1)
    def test_incomplete_output_no_throughput_credit(self):
        r=self.call([{**self.rows[0],'output_verified':False},self.rows[1]]);self.assertEqual(r['details']['throughput_per_second'],'1000000000/21');self.assertEqual(r['report']['status'],'BLOCKED')
    def test_queue_delay(self):self.assertIn('H7_QUEUE_BUDGET',self.codes(self.call(p=replace(self.p,max_queue_ns=1))))
    def test_boolean_success_rejected(self):self.error('H7_JOB_VERDICT_TYPE',self.call,[{**self.rows[0],'output_verified':1},self.rows[1]])
    def test_normal_folder_is_not_cgroup(self):self.error('H7_NOT_CGROUP2',CgroupScope,self.root,self.p)
    def test_budget_exceeded(self):self.error('H7_JOB_BUDGET',self.call,p=replace(self.p,max_jobs=1))
    def test_sample_is_not_enforcement(self):
        r=observe_group(os.getpgrp());self.assertFalse(r['aggregate_enforced']);self.assertTrue(r['observation_only']);self.assertGreater(r['sampled_rss_sum'],0)
    def test_real_descendant_rss(self):
        code="import subprocess,sys,time; a=bytearray(2000000); p=subprocess.Popen([sys.executable,'-c','import time; a=bytearray(3000000); time.sleep(5)']); print(p.pid,flush=True); time.sleep(5)"
        p=subprocess.Popen([sys.executable,'-I','-B','-c',code],stdout=subprocess.PIPE,start_new_session=True,text=True,env={**os.environ,'OAI_IS_JUPYTER_KERNEL':'0'})
        try:
            pid=int(p.stdout.readline());time.sleep(.1);r=observe_group(p.pid)
            self.assertEqual({x['pid'] for x in r['processes']},{p.pid,pid});self.assertGreater(r['sampled_rss_sum'],5000000)
        finally:os.killpg(p.pid,9);p.wait();p.stdout.close()
