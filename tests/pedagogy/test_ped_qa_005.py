import unittest
from bie.pedagogy.pedagogy_benchmark import benchmark_pedagogy

class TestPedagogyBenchmark(unittest.TestCase):
    def test_critical_failure_blocks(self):
        r=benchmark_pedagogy(
            {"objective_coverage":.7,"assessment_alignment":.9},
            {"objective_coverage":.8,"assessment_alignment":.8})
        self.assertFalse(r.passed)
        self.assertIn("objective_coverage",r.failed_metrics)

    def test_all_thresholds_pass(self):
        self.assertTrue(benchmark_pedagogy(
            {"objective_coverage":.9,"assessment_alignment":.9},
            {"objective_coverage":.8,"assessment_alignment":.8}).passed)
