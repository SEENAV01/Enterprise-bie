"""Independent expected-value and metamorphic tests for bounded domain profiles."""
from copy import deepcopy
import unittest
from bie.evaluation.benchmarks.models import BenchmarkError
from bie.evaluation.benchmarks.runner import load_pack, reference_output, grade_case


def q(v, unit): return {'value': v, 'unit': unit}
def vec(v, unit): return {'values': list(v), 'unit': unit}

class DomainBase(unittest.TestCase):
    def code(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BenchmarkError) as ctx: fn(*args, **kwargs)
        self.assertEqual(expected, ctx.exception.code)
    def replay_pack(self, task):
        cases = load_pack(task)
        self.assertEqual(10, len(cases))
        for c in cases:
            with self.subTest(case_id=c.case_id):
                self.assertEqual('DEVELOPMENT', c.split)
                self.assertEqual('AUTHORED_DIAGNOSTIC', c.evidence_grade)
                self.assertEqual('PASS', grade_case(c, reference_output(c.task_id, c.inputs))['status'])
    def mutant(self, task, index, path, value):
        c = load_pack(task)[index]
        answer = deepcopy(c.expected)
        current = answer
        for key in path[:-1]: current = current[key]
        current[path[-1]] = value
        self.assertEqual('FAIL', grade_case(c, answer)['status'])
