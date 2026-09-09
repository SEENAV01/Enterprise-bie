import unittest
from enterprise.queue_worker_consumer import *
from enterprise.fake_queue import *
from enterprise.fake_runtime import *

def message(maxd=3):
    return Msg("t1","r1","REASONING",1,"idem",["python"],["src"],maxd)

def setup(runtime=None,events=None,maxd=3):
    q=FakeDurableQueue([message(maxd)])
    ev=events if events is not None else []
    rt=runtime or FakeWorkerRuntime(events=ev)
    req={"REASONING":object()}
    def ex(ctx): return Result(["out"],["evidence"])
    def commit(ctx,res): ev.append("COMMIT_CALLBACK")
    c=QueueWorkerConsumer(q,rt,req,{"REASONING":ex},{"REASONING":commit},{"REASONING":"RE"},RetryPolicy(1,8,2))
    return q,rt,c,ev

class ConsumerTests(unittest.TestCase):
    def test_success_ack_after_commit(self):
        q,rt,c,ev=setup()
        r=c.consume_one("consumer",["python"],10)
        self.assertEqual(r.outcome,"ACKED")
        self.assertEqual(q.messages["t1"]["state"],"ACKED")
        self.assertLess(ev.index("COMMIT_CALLBACK"), len(ev))

    def test_runtime_failure_not_acked(self):
        q=FakeDurableQueue([message()])
        rt=FakeWorkerRuntime(fail=True)
        c=QueueWorkerConsumer(q,rt,{"REASONING":object()},{"REASONING":lambda c:Result(["o"],["e"])},{"REASONING":lambda c,r:None},{"REASONING":"RE"})
        r=c.consume_one("w",["python"])
        self.assertEqual(r.outcome,"RETRY")
        self.assertNotEqual(q.messages["t1"]["state"],"ACKED")

    def test_commit_failure_not_acked(self):
        q=FakeDurableQueue([message()])
        rt=FakeWorkerRuntime(commit_fail=True)
        c=QueueWorkerConsumer(q,rt,{"REASONING":object()},{"REASONING":lambda c:Result(["o"],["e"])},{"REASONING":lambda c,r:None},{"REASONING":"RE"})
        r=c.consume_one("w",["python"])
        self.assertEqual(r.outcome,"RETRY")
        self.assertNotEqual(q.messages["t1"]["state"],"ACKED")

    def test_missing_executor_dead_letters(self):
        q=FakeDurableQueue([message()])
        c=QueueWorkerConsumer(q,FakeWorkerRuntime(),{"REASONING":object()},{},{"REASONING":lambda c,r:None},{"REASONING":"RE"})
        r=c.consume_one("w",["python"])
        self.assertEqual(r.outcome,"DEAD_LETTER")
        self.assertEqual(q.messages["t1"]["state"],"DEAD_LETTER")

    def test_missing_requirement_dead_letters(self):
        q=FakeDurableQueue([message()])
        c=QueueWorkerConsumer(q,FakeWorkerRuntime(),{},{"REASONING":lambda c:Result(["o"],["e"])},{"REASONING":lambda c,r:None},{"REASONING":"RE"})
        r=c.consume_one("w",["python"])
        self.assertEqual(r.outcome,"DEAD_LETTER")

    def test_retry_policy_exponential_and_capped(self):
        p=RetryPolicy(1,5,2)
        self.assertEqual(p.delay_for_delivery(1),1)
        self.assertEqual(p.delay_for_delivery(2),2)
        self.assertEqual(p.delay_for_delivery(4),5)

    def test_max_delivery_becomes_dead_letter(self):
        q=FakeDurableQueue([message(maxd=1)])
        rt=FakeWorkerRuntime(fail=True)
        c=QueueWorkerConsumer(q,rt,{"REASONING":object()},{"REASONING":lambda c:Result(["o"],["e"])},{"REASONING":lambda c,r:None},{"REASONING":"RE"})
        r=c.consume_one("w",["python"])
        self.assertEqual(r.outcome,"DEAD_LETTER")
        self.assertEqual(q.messages["t1"]["state"],"DEAD_LETTER")

    def test_capability_filter_prevents_delivery(self):
        q,rt,c,ev=setup()
        self.assertIsNone(c.consume_one("w",["gpu"]))

    def test_batch_consumption(self):
        q=FakeDurableQueue([message(),Msg("t2","r1","REASONING",1,"idem2",["python"],["src"],3)])
        rt=FakeWorkerRuntime()
        c=QueueWorkerConsumer(q,rt,{"REASONING":object()},{"REASONING":lambda c:Result(["o"],["e"])},{"REASONING":lambda c,r:None},{"REASONING":"RE"})
        out=c.run_batch("w",["python"],max_messages=5)
        self.assertEqual(len(out),2)
        self.assertTrue(all(x.outcome=="ACKED" for x in out))

    def test_delivery_count_distinct_from_stage_attempt(self):
        q=FakeDurableQueue([message()])
        rt=FakeWorkerRuntime(fail=True)
        c=QueueWorkerConsumer(q,rt,{"REASONING":object()},{"REASONING":lambda c:Result(["o"],["e"])},{"REASONING":lambda c,r:None},{"REASONING":"RE"})
        r1=c.consume_one("w",["python"])
        r2=c.consume_one("w",["python"])
        self.assertEqual(r2.delivery_count,2)
        self.assertEqual(q.messages["t1"]["msg"].attempt,1)

if __name__=="__main__":unittest.main()
