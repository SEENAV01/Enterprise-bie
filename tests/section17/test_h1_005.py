import unittest
from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError, digest, canonical_json, strict_loads

import os,time,multiprocessing
from bie.evaluation.benchmarks.release.supervised import SupervisedProvider
from bie.evaluation.benchmarks.release import model
from batch005_helpers import FixtureProvider,judgement_fixture
class SimpleFactory:
    def __call__(self):return FixtureProvider()
class SleepProvider(FixtureProvider):
    def complete(self,request):time.sleep(30);return '{}'
class SleepFactory:
    def __call__(self):return SleepProvider()
class CrashProvider(FixtureProvider):
    def complete(self,request):os._exit(7)
class CrashFactory:
    def __call__(self):return CrashProvider()
class ErrorFactory:
    def __call__(self):return FixtureProvider(error=RuntimeError('secret-in-worker'))
class HugeFactory:
    def __call__(self):return FixtureProvider(raw='x'*128001)
class WrongFactory:
    def __call__(self):
        p=FixtureProvider();p.provider_id='wrong';return p
class SupervisedDeadline(unittest.TestCase):
    def port(self,factory=None,**kw):return SupervisedProvider(factory or SimpleFactory(),provider_id='fixture-provider',model_version='fixture-v1',fixture_only=True,**kw)
    def execute(self,p):
        c,rub,r,candidate,_=judgement_fixture()
        return model.execute(c,rub,r,candidate,provider=p,provider_id=p.provider_id,model_version=p.model_version,assessor_id='model')
    def test_positive_process_roundtrip(self):
        p=self.port(timeout_seconds=5);o=self.execute(p);self.assertEqual('MEASURED',o['status']);self.assertEqual('FIXTURE',o['execution']);self.assertTrue(p.last_observation['worker_reaped'])
    def test_hanging_worker_is_killed_and_reaped(self):
        p=self.port(SleepFactory(),timeout_seconds=.2);start=time.monotonic();o=self.execute(p)
        self.assertIn('MODEL_PROVIDER_DEADLINE_EXCEEDED',o['reasons']);self.assertTrue(p.last_observation['worker_reaped']);self.assertLess(time.monotonic()-start,4)
    def test_worker_crash_blocks(self):self.assertEqual('BLOCKED',self.execute(self.port(CrashFactory(),timeout_seconds=5))['status'])
    def test_secret_exception_is_not_returned(self):
        o=self.execute(self.port(ErrorFactory(),timeout_seconds=5));self.assertNotIn('secret-in-worker',canonical_json(o));self.assertEqual('BLOCKED',o['status'])
    def test_oversized_response_blocks(self):self.assertEqual('BLOCKED',self.execute(self.port(HugeFactory(),timeout_seconds=5))['status'])
    def test_wrong_child_identity_blocks(self):self.assertEqual('BLOCKED',self.execute(self.port(WrongFactory(),timeout_seconds=5))['status'])
    def test_nan_deadline_refused(self):
        with self.assertRaises(BenchmarkError):self.port(timeout_seconds=float('nan'))
    def test_bool_deadline_refused(self):
        with self.assertRaises(BenchmarkError):self.port(timeout_seconds=True)
    def test_zero_deadline_refused(self):
        with self.assertRaises(BenchmarkError):self.port(timeout_seconds=0)
    def test_overlarge_deadline_refused(self):
        with self.assertRaises(BenchmarkError):self.port(timeout_seconds=301)
    def test_response_budget_bound(self):
        with self.assertRaises(BenchmarkError):self.port(response_limit=128001)
    def test_noncallable_factory_refused(self):
        with self.assertRaises(BenchmarkError):SupervisedProvider(42,provider_id='p',model_version='v',fixture_only=True)
    def test_repeat_timeout_leaves_no_children(self):
        before={p.pid for p in multiprocessing.active_children()}
        for _ in range(2):self.execute(self.port(SleepFactory(),timeout_seconds=.1))
        self.assertEqual(before,{p.pid for p in multiprocessing.active_children()})
