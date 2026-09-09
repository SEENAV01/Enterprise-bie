import unittest
from dataclasses import asdict
from bie.infrastructure.run_state import build_run_state
from bie.infrastructure.worker_scheduler import CapabilityScheduler, WorkerCapabilities, StageResourceRequirement

class RepositoryIntegrationTests(unittest.TestCase):
    def test_retry_does_not_rewrite_failed_attempt_evidence(self):
        state=build_run_state('run',{'SOURCE':[]})
        state.mark_ready('SOURCE');state.start('SOURCE',[])
        state.fail('SOURCE',['source unavailable'],['failure-evidence'],'BI')
        old=state.stages['SOURCE'].current
        snapshot=asdict(old)
        state.retry('SOURCE')
        self.assertEqual(asdict(old),snapshot)
        self.assertEqual(old.state,'FAILED')
        self.assertEqual(state.stages['SOURCE'].current.attempt,2)
        self.assertEqual(state.stages['SOURCE'].current.state,'READY')
        state.validate()

    def test_worker_capacity_survives_executor_integration(self):
        scheduler=CapabilityScheduler([WorkerCapabilities('worker',{'python'},4,8,max_concurrency=2)])
        requirement=StageResourceRequirement('REASONING',{'python'},slot_cost=1)
        selection=scheduler.select(requirement)
        self.assertEqual(scheduler.reserve(selection,requirement).active_slots,1)
        self.assertEqual(scheduler.reserve(scheduler.select(requirement),requirement).active_slots,2)
        self.assertEqual(scheduler.release('worker').active_slots,1)

if __name__=='__main__':unittest.main()
