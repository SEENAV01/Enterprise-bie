import unittest
from bie.visual_intelligence.realbook_fixtures import *
from bie.visual_intelligence.visual_benchmark_hardened import *
def obs(f,emp=True):return BenchmarkObservation(f.fixture_id,f.expected_representation,f.expected_grammar,.95,.9,.95,True,True,emp)
class T(unittest.TestCase):
 def test_nonempirical_notrun(self):
  fs=reference_nonacceptance_fixtures();os=[obs(f,None) for f in fs];r=run_benchmark(fs,os,require_empirical=True);self.assertTrue(r.not_run);self.assertFalse(r.passed)
 def test_pass_without_empirical_requirement(self):
  fs=reference_nonacceptance_fixtures();os=[obs(f,None) for f in fs];r=run_benchmark(fs,os,require_empirical=False);self.assertTrue(r.passed)
 def test_rep_fail(self):
  fs=reference_nonacceptance_fixtures();os=[obs(f) for f in fs];os[0]=BenchmarkObservation(fs[0].fixture_id,"wrong",fs[0].expected_grammar,.95,.9,.95,True,True,True);self.assertFalse(run_benchmark(fs,os).passed)
 def test_ground_floor(self):
  fs=reference_nonacceptance_fixtures();os=[obs(f) for f in fs];os[0]=BenchmarkObservation(fs[0].fixture_id,fs[0].expected_representation,fs[0].expected_grammar,.95,.9,.5,True,True,True);self.assertFalse(run_benchmark(fs,os).passed)
 def test_missing_observation(self):
  fs=reference_nonacceptance_fixtures();r=run_benchmark(fs,[obs(f) for f in fs[:-1]]);self.assertTrue(r.not_run)
 def test_mutations(self):self.assertEqual(len(adversarial_mutations(reference_nonacceptance_fixtures()[0])),3)
 def test_not_accepted(self):self.assertFalse(run_benchmark(reference_nonacceptance_fixtures(),[obs(f) for f in reference_nonacceptance_fixtures()]).accepted)
