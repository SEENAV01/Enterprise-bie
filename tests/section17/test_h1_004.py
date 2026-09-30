import unittest
from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError, digest, canonical_json, strict_loads

from batch005_helpers import judgement_fixture,FixtureProvider
from bie.evaluation.benchmarks.release import model
class ModelSnapshotBoundary(unittest.TestCase):
    def setUp(self):self.ctx,self.rub,self.r,self.c,self.units=judgement_fixture()
    def execute(self,p):return model.execute(self.ctx,self.rub,self.r,self.c,provider=p,provider_id='fixture-provider',model_version='fixture-v1',assessor_id='judge')
    def test_positive_fixture_stays_fixture(self):self.assertEqual('FIXTURE',self.execute(FixtureProvider())['execution'])
    def test_fixture_flag_changed_during_call_blocks(self):
        p=FixtureProvider();p.mutator=lambda body:setattr(p,'fixture_only',False)
        self.assertIn('MODEL_PROVIDER_CHANGED_DURING_CALL',self.execute(p)['reasons'])
    def test_fixture_flag_changed_to_integer_blocks(self):
        p=FixtureProvider();p.mutator=lambda body:setattr(p,'fixture_only',1)
        self.assertEqual('BLOCKED',self.execute(p)['status'])
    def test_provider_identity_changed_blocks(self):
        p=FixtureProvider();p.mutator=lambda body:setattr(p,'provider_id','other')
        self.assertEqual('BLOCKED',self.execute(p)['status'])
    def test_context_mutation_cannot_rebind_assessment(self):
        old=deepcopy(self.ctx);p=FixtureProvider(mutator=lambda body:self.ctx.update(candidate_sha256=digest('other')))
        self.assertEqual(old,self.execute(p)['context'])
    def test_rubric_mutation_cannot_change_denominator(self):
        units=deepcopy(self.units);units[0]['credit']='0'
        p=FixtureProvider(units=units,mutator=lambda body:self.rub['units'][0].update(weight='1'))
        self.assertEqual('1/4',self.execute(p)['score_exact'])
    def test_request_candidate_is_copied(self):
        p=FixtureProvider();self.execute(p);p.last_request['candidate_data']['answer']='modified'
        self.assertEqual('Conservation with consistent units',self.c['answer'])
    def test_request_reference_is_copied(self):
        p=FixtureProvider();self.execute(p);p.last_request['reference_data'].clear();self.assertTrue(self.r)
    def test_missing_provider_still_blocked(self):self.assertEqual('BLOCKED',self.execute(None)['status'])
    def test_missing_units_still_blocked(self):
        self.assertEqual('BLOCKED',self.execute(FixtureProvider(units=[]))['status'])
    def test_duplicate_json_keys_still_blocked(self):
        self.assertEqual('BLOCKED',self.execute(FixtureProvider(raw='{"x":1,"x":2}'))['status'])
    def test_unexpected_error_redacted(self):
        o=self.execute(FixtureProvider(error=RuntimeError('my-secret')))
        self.assertEqual('BLOCKED',o['status']);self.assertNotIn('my-secret',canonical_json(o))
