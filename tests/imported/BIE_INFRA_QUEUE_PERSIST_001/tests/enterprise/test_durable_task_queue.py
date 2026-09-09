import unittest, tempfile, sqlite3
from pathlib import Path
from bie.infrastructure.durable_task_queue import *

class FakeClock:
    def __init__(self):self.t=100.0
    def __call__(self):return self.t
    def advance(self,x):self.t+=x

def msg(i="t1",priority=100,max_deliveries=3,caps=None):
    return DurableTaskMessage(i,"r","S",1,"idem-"+i,list(caps or ["python"]),["a"],priority,max_deliveries,0)

class DurableQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.clock=FakeClock()
        self.path=Path(self.tmp.name)/"queue.db"
        self.q=SQLiteDurableTaskQueue(self.path,self.clock,max_queued=5,max_in_flight=2)
    def tearDown(self): self.tmp.cleanup()

    def test_ready_survives_restart(self):
        self.q.enqueue(msg())
        q2=SQLiteDurableTaskQueue(self.path,self.clock,max_queued=5,max_in_flight=2)
        self.assertEqual(q2.get("t1").state,"READY")

    def test_delivered_survives_restart(self):
        self.q.enqueue(msg()); self.q.poll("w1",10,["python"])
        q2=SQLiteDurableTaskQueue(self.path,self.clock,max_queued=5,max_in_flight=2)
        self.assertEqual(q2.get("t1").state,"DELIVERED")

    def test_visibility_recovery_after_restart(self):
        self.q.enqueue(msg()); self.q.poll("w1",5,["python"])
        self.clock.advance(6)
        q2=SQLiteDurableTaskQueue(self.path,self.clock,max_queued=5,max_in_flight=2)
        self.assertEqual(q2.recover_expired(),1)
        self.assertEqual(q2.get("t1").state,"READY")

    def test_max_delivery_dead_letter_persists(self):
        self.q.enqueue(msg(max_deliveries=1)); self.q.poll("w1",5,["python"])
        self.clock.advance(6); self.q.recover_expired()
        q2=SQLiteDurableTaskQueue(self.path,self.clock)
        self.assertEqual(q2.get("t1").state,"DEAD_LETTER")

    def test_ack_persists_and_no_redelivery(self):
        self.q.enqueue(msg()); self.q.poll("w1",5,["python"]); self.q.ack("t1","w1")
        q2=SQLiteDurableTaskQueue(self.path,self.clock)
        self.assertEqual(q2.get("t1").state,"ACKED")
        self.assertIsNone(q2.poll("w2",5,["python"]))

    def test_delivery_count_durable(self):
        self.q.enqueue(msg()); self.q.poll("w1",1,["python"])
        self.clock.advance(2); self.q.poll("w2",1,["python"])
        self.assertEqual(self.q.get("t1").delivery_count,2)

    def test_idempotent_duplicate_enqueue(self):
        m=msg(); self.q.enqueue(m); self.q.enqueue(m)
        self.assertEqual(self.q.stats()["READY"],1)

    def test_conflicting_task_id_rejected(self):
        self.q.enqueue(msg())
        bad=DurableTaskMessage("t1","r","OTHER",1,"other",["python"],["a"])
        with self.assertRaises(DurableQueueError): self.q.enqueue(bad)

    def test_capability_routing(self):
        self.q.enqueue(msg(caps=["gpu"]))
        self.assertIsNone(self.q.poll("cpu",5,["python"]))
        self.assertEqual(self.q.poll("gpu",5,["gpu"]).task.task_id,"t1")

    def test_priority_order(self):
        self.q.enqueue(msg("low",100)); self.q.enqueue(msg("high",1))
        self.assertEqual(self.q.poll("w",5,["python"]).task.task_id,"high")

    def test_wrong_consumer_cannot_ack(self):
        self.q.enqueue(msg()); self.q.poll("w1",5,["python"])
        with self.assertRaises(DurableQueueError): self.q.ack("t1","w2")

    def test_nack_and_dead_letter_storage(self):
        self.q.enqueue(msg(max_deliveries=1)); self.q.poll("w1",5,["python"])
        self.q.nack("t1","w1",reason="failed")
        self.assertEqual(self.q.get("t1").state,"DEAD_LETTER")
        self.assertIn("DEAD_LETTERED",[e["event_type"] for e in self.q.events("t1")])

    def test_manual_redrive_persists(self):
        self.q.enqueue(msg()); self.q.dead_letter("t1","manual"); self.q.redrive("t1")
        q2=SQLiteDurableTaskQueue(self.path,self.clock)
        self.assertEqual(q2.get("t1").state,"READY")

    def test_backpressure_persists(self):
        q=SQLiteDurableTaskQueue(Path(self.tmp.name)/"bp.db",self.clock,max_queued=1,max_in_flight=1)
        q.enqueue(msg("a"))
        with self.assertRaises(DurableQueueError): q.enqueue(msg("b"))

    def test_schema_version_fail_closed(self):
        bad=Path(self.tmp.name)/"bad.db"
        c=sqlite3.connect(bad)
        c.execute("CREATE TABLE schema_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        c.execute("INSERT INTO schema_meta VALUES('schema_version','999')")
        c.commit(); c.close()
        with self.assertRaises(DurableQueueError): SQLiteDurableTaskQueue(bad,self.clock)

if __name__=="__main__":unittest.main()
