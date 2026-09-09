import unittest
from bie.infrastructure.worker_scheduler import *

def worker(wid,caps,cpu=8,mem=16,gpu=False,vram=0,mc=2,aff=None):
    return WorkerCapabilities(wid,set(caps),cpu,mem,gpu,vram,mc,set(aff or []))

class WorkerSchedulerTests(unittest.TestCase):
    def test_capability_match(self):
        s=CapabilityScheduler([worker("w1",["python","node"])])
        r=StageResourceRequirement("REASONING",{"python"},2,4)
        self.assertEqual(s.select(r).worker_id,"w1")

    def test_missing_capability_rejected(self):
        s=CapabilityScheduler([worker("w1",["python"])])
        r=StageResourceRequirement("VIDEO_RENDER",{"remotion_render"},2,4)
        with self.assertRaises(WorkerSchedulingError):s.select(r)

    def test_gpu_hard_requirement(self):
        s=CapabilityScheduler([worker("cpu",["node"],gpu=False),worker("gpu",["node"],gpu=True,vram=12)])
        r=StageResourceRequirement("VIDEO_RENDER",{"node"},2,4,True,8)
        self.assertEqual(s.select(r).worker_id,"gpu")

    def test_gpu_vram_floor(self):
        s=CapabilityScheduler([worker("gpu",["node"],gpu=True,vram=4)])
        r=StageResourceRequirement("X",{"node"},1,1,True,8)
        with self.assertRaises(WorkerSchedulingError):s.select(r)

    def test_concurrency_not_overcommitted(self):
        w=worker("w",["python"],mc=1)
        s=CapabilityScheduler([w],{"w":WorkerLoad("w",1,True)})
        with self.assertRaises(WorkerSchedulingError):s.select(StageResourceRequirement("R",{"python"}))

    def test_unhealthy_worker_rejected(self):
        s=CapabilityScheduler([worker("w",["python"])],{"w":WorkerLoad("w",0,False)})
        with self.assertRaises(WorkerSchedulingError):s.select(StageResourceRequirement("R",{"python"}))

    def test_affinity_preferred(self):
        s=CapabilityScheduler([worker("a",["python"],aff=["book-1"]),worker("b",["python"])])
        r=StageResourceRequirement("R",{"python"},preferred_affinity_tags={"book-1"})
        self.assertEqual(s.select(r).worker_id,"a")

    def test_deterministic_tie_break(self):
        s=CapabilityScheduler([worker("b",["python"]),worker("a",["python"])])
        r=StageResourceRequirement("R",{"python"})
        self.assertEqual(s.select(r).worker_id,"a")

    def test_reserve_release(self):
        s=CapabilityScheduler([worker("w",["python"],mc=2)])
        r=StageResourceRequirement("R",{"python"})
        sel=s.select(r); s.reserve(sel,r)
        self.assertEqual(s.loads["w"].active_slots,1)
        s.release("w")
        self.assertEqual(s.loads["w"].active_slots,0)

    def test_sandbox_required(self):
        s=CapabilityScheduler([worker("w",["browser_runtime"])])
        r=StageResourceRequirement("GAME_RUNTIME",{"browser_runtime"},requires_sandbox=True)
        with self.assertRaises(WorkerSchedulingError):s.select(r)

    def test_invalid_vram_requirement(self):
        with self.assertRaises(WorkerSchedulingError):
            StageResourceRequirement("X",set(),min_gpu_vram_gb=4,requires_gpu=False).validate()

if __name__=="__main__":unittest.main()
