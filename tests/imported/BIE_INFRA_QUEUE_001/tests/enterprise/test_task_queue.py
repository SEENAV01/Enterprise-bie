import unittest
from bie.infrastructure.task_queue import *

class FakeClock:
    def __init__(self):self.t=100.0
    def __call__(self):return self.t
    def advance(self,x):self.t+=x

def msg(i="t1",priority=100,max_deliveries=3,caps=None):
    return TaskMessage(i,"r","S",1,"idem-"+i,list(caps or ["python"]),["a"],priority,max_deliveries,0)

class QueueTests(unittest.TestCase):
    def setUp(self):
        self.clock=FakeClock()
        self.q=InMemoryDurableQueue(self.clock,max_queued=5,max_in_flight=2)

    def test_enqueue_poll_ack(self):
        self.q.enqueue(msg())
        d=self.q.poll("w1",10,["python"])
        self.assertEqual(d.task.task_id,"t1")
        self.q.ack("t1","w1")
        self.assertEqual(self.q.state("t1"),"ACKED")

    def test_visibility_timeout_redelivery(self):
        self.q.enqueue(msg())
        self.q.poll("w1",5,["python"])
        self.clock.advance(6)
        d=self.q.poll("w2",5,["python"])
        self.assertEqual(d.delivery_count,2)
        self.assertEqual(d.consumer_id,"w2")

    def test_wrong_consumer_cannot_ack(self):
        self.q.enqueue(msg())
        self.q.poll("w1",5,["python"])
        with self.assertRaises(QueueError):self.q.ack("t1","w2")

    def test_nack_requeues(self):
        self.q.enqueue(msg())
        self.q.poll("w1",5,["python"])
        self.q.nack("t1","w1",reason="retryable")
        self.assertEqual(self.q.state("t1"),"READY")

    def test_max_deliveries_dead_letter(self):
        self.q.enqueue(msg(max_deliveries=2))
        self.q.poll("w1",1,["python"]); self.clock.advance(2)
        self.q.poll("w2",1,["python"]); self.clock.advance(2)
        self.assertEqual(self.q.state("t1"),"DEAD_LETTER")

    def test_priority_order(self):
        self.q.enqueue(msg("low",100)); self.q.enqueue(msg("high",1))
        self.assertEqual(self.q.poll("w",5,["python"]).task.task_id,"high")

    def test_capability_routing(self):
        self.q.enqueue(msg(caps=["gpu"]))
        self.assertIsNone(self.q.poll("cpu",5,["python"]))
        self.assertEqual(self.q.poll("gpu",5,["gpu"]).task.task_id,"t1")

    def test_backpressure(self):
        q=InMemoryDurableQueue(self.clock,max_queued=1,max_in_flight=1)
        q.enqueue(msg("a"))
        with self.assertRaises(QueueError):q.enqueue(msg("b"))

    def test_inflight_backpressure(self):
        q=InMemoryDurableQueue(self.clock,max_queued=5,max_in_flight=1)
        q.enqueue(msg("a")); q.enqueue(msg("b"))
        self.assertIsNotNone(q.poll("w1",10,["python"]))
        self.assertIsNone(q.poll("w2",10,["python"]))

    def test_idempotent_same_enqueue(self):
        m=msg()
        self.q.enqueue(m); self.q.enqueue(m)
        self.assertEqual(len(self.q.records),1)

    def test_conflicting_task_id_rejected(self):
        self.q.enqueue(msg())
        bad=TaskMessage("t1","r","OTHER",1,"different",["python"],["a"])
        with self.assertRaises(QueueError):self.q.enqueue(bad)

    def test_manual_redrive(self):
        self.q.enqueue(msg())
        self.q.dead_letter("t1","manual")
        self.q.redrive("t1")
        self.assertEqual(self.q.state("t1"),"READY")

if __name__=="__main__":unittest.main()
