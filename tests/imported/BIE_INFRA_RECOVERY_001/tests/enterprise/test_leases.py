import unittest
from bie.infrastructure.leases import *

class FakeClock:
    def __init__(self):self.t=1000.0
    def __call__(self):return self.t
    def advance(self,x):self.t+=x

class LeaseTests(unittest.TestCase):
    def setUp(self):
        self.clock=FakeClock()
        self.m=LeaseManager(self.clock)
        self.k=LeaseKey("r","S",1)

    def test_acquire(self):
        t=self.m.acquire(self.k,"w1",10)
        self.assertEqual(t.fencing_token,1)
        self.m.commit_guard(t)

    def test_duplicate_active_lease_rejected(self):
        self.m.acquire(self.k,"w1",10)
        with self.assertRaises(LeaseError):self.m.acquire(self.k,"w2",10)

    def test_renew(self):
        t=self.m.acquire(self.k,"w1",10)
        self.clock.advance(5)
        r=self.m.renew(t,20)
        self.assertEqual(r.fencing_token,t.fencing_token)
        self.assertGreater(r.expires_at,t.expires_at)

    def test_expired_commit_rejected(self):
        t=self.m.acquire(self.k,"w1",10)
        self.clock.advance(10)
        with self.assertRaises(LeaseError):self.m.commit_guard(t)

    def test_takeover_increments_fence(self):
        t1=self.m.acquire(self.k,"w1",5)
        self.clock.advance(6)
        t2=self.m.acquire(self.k,"w2",5)
        self.assertEqual(t2.fencing_token,2)
        with self.assertRaises(LeaseError):self.m.commit_guard(t1)

    def test_recovery_evidence_created_on_takeover(self):
        self.m.acquire(self.k,"w1",5)
        self.clock.advance(6)
        self.m.acquire(self.k,"w2",5)
        ev=self.m.recovery_evidence()
        self.assertEqual(len(ev),1)
        self.assertEqual(ev[0].previous_worker_id,"w1")

    def test_release(self):
        t=self.m.acquire(self.k,"w1",5)
        self.m.release(t)
        self.assertIsNone(self.m.active_lease(self.k))

    def test_foreign_worker_rejected(self):
        t=self.m.acquire(self.k,"w1",10)
        fake=LeaseToken(self.k,"w2",t.fencing_token,t.acquired_at,t.expires_at)
        with self.assertRaises(LeaseError):self.m.commit_guard(fake)

    def test_scope_guard(self):
        t=self.m.acquire(self.k,"w1",10)
        g=WorkerOwnershipGuard(self.m)
        g.authorize_state_write(t,"r","S",1)
        with self.assertRaises(LeaseError):g.authorize_state_write(t,"r","OTHER",1)

    def test_explicit_recovery(self):
        self.m.acquire(self.k,"w1",5)
        self.clock.advance(6)
        ev=self.m.mark_expired_recoverable(self.k)
        self.assertEqual(ev.reason,"lease_expired")
        self.assertIsNone(self.m.active_lease(self.k))

if __name__=="__main__":unittest.main()
