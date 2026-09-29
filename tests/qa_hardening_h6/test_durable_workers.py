from h6_helpers import *
import threading,multiprocessing

def concurrent_claim(payload):
 d=strict_json(payload);j=LeaseJournal(d['path'],Binding(**d['binding']),LeasePolicy(**d['policy']))
 try:return canonical_bytes(j.claim('job',digest('effect'),d['owner'],NOW))
 except ContractError as e:return canonical_bytes({'error':e.code})

class Durable(Temp):
 def journal(self,policy=None):
  self.p=policy or LeasePolicy(attempts=2,lease_seconds=10);self.b=bound(self.p);return LeaseJournal(self.root/'journal.sqlite',self.b,self.p)
 def claim(self,j,now=NOW):return j.claim('job',digest('effect'),'owner',now)
 def test_durable_reopen(self):
  j=self.journal();self.claim(j);j=LeaseJournal(self.root/'journal.sqlite',self.b,self.p);self.assertEqual(j.export()['jobs'][0]['attempts'],1)
 def test_busy_lease(self):
  j=self.journal();self.claim(j);self.error('H6_LEASE_BUSY',self.claim,j)
 def test_expired_recovery_consumes_attempt(self):
  j=self.journal();self.claim(j);claim=self.claim(j,NOW+10);self.assertEqual(claim['token'],2);self.assertEqual(claim['attempt'],2)
 def test_stale_owner_cannot_finish(self):
  j=self.journal();self.claim(j);self.claim(j,NOW+10);self.error('H6_STALE_FENCE',j.finish,'job',1,'owner',NOW+11,digest('result'),('render',))
 def test_budget_survives_reopen(self):
  j=self.journal();self.claim(j);self.claim(j,NOW+10);j=LeaseJournal(self.root/'journal.sqlite',self.b,self.p);self.error('H6_ATTEMPT_BUDGET',self.claim,j,NOW+20)
 def test_result_and_outbox_are_atomic(self):
  j=self.journal();r=self.claim(j);payload=j.finish('job',r['token'],'owner',NOW+1,digest('result'),('render','semantic'));self.assertEqual(j.pending(),[payload]);self.assertEqual(j.export()['jobs'][0]['state'],'FINISHED')
 def test_duplicate_delivery_no_second_outbox(self):
  j=self.journal();r=self.claim(j);j.finish('job',1,'owner',NOW+1,digest('result'),('render',));again=self.claim(j,NOW+2);self.assertTrue(again['replayed']);self.assertEqual(len(j.pending()),1)
 def test_ack_exact_identity(self):
  j=self.journal();self.claim(j);p=j.finish('job',1,'owner',NOW+1,digest('result'),('render',));j.acknowledge('job',digest(p));j.acknowledge('job',digest(p));self.assertEqual(j.pending(),[])
 def test_wrong_ack_blocks(self):
  j=self.journal();self.claim(j);j.finish('job',1,'owner',NOW+1,digest('result'),('render',));self.error('H6_OUTBOX_ACK_IDENTITY',j.acknowledge,'job','0'*64)
 def test_alias_cannot_reset_budget(self):
  j=self.journal();self.claim(j);self.error('H6_EFFECT_ALIAS',j.claim,'new-job',digest('effect'),'owner',NOW+11)
 def test_changed_effect_rejected(self):
  j=self.journal();self.claim(j);self.error('H6_JOB_EFFECT_CHANGED',j.claim,'job',digest('different'),'owner',NOW+11)
 def test_heartbeat_renews(self):
  j=self.journal();self.claim(j);j.heartbeat('job',1,'owner',NOW+9);self.error('H6_LEASE_BUSY',self.claim,j,NOW+10)
 def test_expired_heartbeat_rejected(self):
  j=self.journal();self.claim(j);self.error('H6_LEASE_EXPIRED',j.heartbeat,'job',1,'owner',NOW+10)
 def test_wrong_owner_rejected(self):
  j=self.journal();self.claim(j);self.error('H6_STALE_FENCE',j.heartbeat,'job',1,'other',NOW+1)
 def test_clock_rollback(self):
  j=self.journal();self.claim(j);self.error('H6_CLOCK_ROLLBACK',self.claim,j,NOW-1)
 def test_cancel_fences_and_blocks_recovery(self):
  j=self.journal();self.claim(j);j.cancel('job',NOW+1);self.error('H6_JOB_CANCELLED',self.claim,j,NOW+20)
 def test_cancelled_cannot_finish(self):
  j=self.journal();self.claim(j);j.cancel('job',NOW+1);self.error('H6_STALE_FENCE',j.finish,'job',1,'owner',NOW+2,digest('result'),('render',))
 def test_changed_context_rejected(self):
  j=self.journal();self.error('H6_JOURNAL_CONTEXT_CHANGED',LeaseJournal,self.root/'journal.sqlite',replace(self.b,run_id='other'),self.p)
 def test_job_counter_tamper_detected(self):
  j=self.journal();self.claim(j)
  import sqlite3
  with sqlite3.connect(j.path) as db:db.execute('UPDATE jobs SET attempt=0')
  self.error('H6_JOURNAL_STATE_CHANGED',j.export)
 def test_event_tamper_detected(self):
  j=self.journal();self.claim(j)
  import sqlite3
  with sqlite3.connect(j.path) as db:db.execute("UPDATE events SET body='{}'")
  self.error('H6_JOURNAL_CHAIN',j.export)
 def test_event_deletion_detected(self):
  j=self.journal();self.claim(j)
  import sqlite3
  with sqlite3.connect(j.path) as db:db.execute('DELETE FROM events')
  self.error('H6_JOURNAL_EVENT_MISSING',j.export)
 def test_link_rejected(self):
  p=self.root/'actual';p.write_bytes(b'');(self.root/'journal.sqlite').symlink_to(p)
  with self.assertRaises(ContractError):self.journal()
 def test_concurrent_reservations_one_winner(self):
  j=self.journal();payloads=[canonical_bytes(dict(path=str(j.path),binding=asdict(self.b),policy=asdict(self.p),owner='owner-'+str(i))) for i in range(2)]
  from concurrent.futures import ThreadPoolExecutor
  with ThreadPoolExecutor(2) as pool:rows=list(pool.map(concurrent_claim,payloads))
  rows=[strict_json(x) for x in rows];self.assertEqual(sum(r.get('state')=='RUNNING' for r in rows),1);self.assertEqual(j.export()['jobs'][0]['attempts'],1)

class NativeInvalidation(Temp):
 def test_transitive_native_closure(self):
  g={'source':(),'semantic':('source',),'render':('semantic',),'unrelated':()};s={k:'VERIFIED' for k in g}
  r=native_invalidations(g,s,('source',),'source repair');self.assertEqual(r['affected_task_ids'],['render','semantic','source']);self.assertFalse(r['dispatch_performed'])
 def test_cycle_rejected(self):
  self.error('H6_INVALIDATION_CYCLE',native_invalidations,{'a':('b',),'b':('a',)},{'a':'VERIFIED','b':'VERIFIED'},('a',),'repair')
 def test_missing_status_rejected(self):
  self.error('H6_INVALIDATION_CENSUS',native_invalidations,{'a':()}, {},('a',),'repair')
 def test_already_invalidated_recorded_not_reset(self):
  r=native_invalidations({'a':()},{'a':'INVALIDATED'},('a',),'repair');self.assertTrue(r['invalidations'][0]['already_invalidated'])
 def test_unknown_task_rejected(self):
  self.error('H6_INVALIDATION_UNKNOWN_TASK',native_invalidations,{'a':()},{'a':'VERIFIED'},('b',),'repair')

class MultipleRootInvalidation(Temp):
 def test_independent_roots_have_exact_causes(self):
  g={'a':(),'b':(),'x':('a',),'y':('b',),'join':('x','y'),'spare':()};r=native_invalidations(g,{k:'VERIFIED' for k in g},('a','b'),'repair')
  rows={x['task_id']:x for x in r['invalidations']};self.assertEqual(rows['y']['source_task_id'],'b');self.assertEqual(rows['join']['source_task_ids'],['a','b']);self.assertIsNone(rows['join']['source_task_id']);self.assertNotIn('spare',rows)
 def test_root_order_cannot_change_causal_attribution(self):
  g={'a':(),'b':(),'join':('a','b')};s={k:'VERIFIED' for k in g}
  self.assertEqual(native_invalidations(g,s,('a','b'),'repair'),native_invalidations(g,s,('b','a'),'repair'))

class Workers(Temp):
 def test_success_records_actual_process(self):
  payload=canonical_bytes({'content':{'records':[]}});out,r=invoke(cb(good_generator),payload);self.assertTrue(r['worker_executed']);self.assertIsNone(r['error']);self.assertEqual(out,b'{"records":[]}')
 def test_exception_blocks(self):
  out,r=invoke(cb(raises_generator),b'{}');self.assertIsNone(out);self.assertEqual(r['error'],'H6_CALLBACK_FAILED')
 def test_timeout_kills(self):
  out,r=invoke(cb(slow_generator),b'{}',timeout=1);self.assertIsNone(out);self.assertEqual(r['error'],'H6_WORKER_TIMEOUT')
 def test_output_budget(self):
  out,r=invoke(cb(huge_generator),b'{}',max_bytes=10);self.assertIsNone(out);self.assertEqual(r['error'],'H6_WORKER_OUTPUT_LIMIT')
 def test_callback_identity(self):
  self.error('H6_CALLBACK_IDENTITY',Callback,'generator','0'*64,good_generator)
 def test_pre_cancelled_no_execution(self):
  e=threading.Event();e.set();self.error('H6_CANCELLED',invoke,cb(good_generator),b'{}',cancel=e)
 def test_running_cancellation(self):
  e=threading.Event();t=threading.Timer(.2,e.set);t.start()
  try:out,r=invoke(cb(slow_generator),b'{}',timeout=5,cancel=e)
  finally:t.cancel()
  self.assertIsNone(out);self.assertEqual(r['error'],'H6_CANCELLED')
