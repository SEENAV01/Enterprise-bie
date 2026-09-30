"""Synthetic unit-test helpers. NOT independently reviewed benchmark evidence."""
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from bie.evaluation.benchmarks.models import BenchmarkCase, BenchmarkError, SourceReference
from bie.evaluation.benchmarks.registry import Registry


def case(case_id='unit.case.1', x=1, **kw):
    defaults=dict(case_id=case_id,task_id='BIE-EVAL-PHY-001',domain='physics',
        title='Synthetic unit fixture',prompt=f'Unit fixture input {x}: compute its structured response.',
        inputs={'x':x},expected={'value':x},split='DEVELOPMENT',leakage_group='group.'+case_id,
        author_id='unit-author',derivation='Synthetic test data, not a scientific gold reference.',
        sources=(SourceReference('unit-source','Unit fixture','Synthetic test only','https://example.test/fixture','Test-only authored input'),),
        tags=('unit-fixture',))
    defaults.update(kw)
    return BenchmarkCase.create(**defaults)

class Base(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.registry=Registry(self.root/'unit.sqlite3')
    def tearDown(self):
        self.registry.close()
        self.temp.cleanup()
    def code(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BenchmarkError) as context:
            fn(*args,**kwargs)
        self.assertEqual(expected,context.exception.code)
    def snapshot(self, cases=None, dataset_id='unit-dataset'):
        from bie.evaluation.benchmarks.versioning import VersionStore
        cases=cases or [case()]
        self.registry.register(cases)
        return VersionStore(self.registry).create(dataset_id,'1.0.0',[c.case_id for c in cases])
