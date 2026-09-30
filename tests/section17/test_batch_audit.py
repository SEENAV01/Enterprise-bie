"""Batch 001 repair regressions. Case counts are not additional atomic tasks."""
from pathlib import Path
from helpers import Base, case
from bie.evaluation.benchmarks.models import canonical_json, digest, strict_loads
from bie.evaluation.benchmarks.anti_gaming import AttemptLedger, leakage_report
from bie.evaluation.benchmarks.governance import Authority
from bie.evaluation.benchmarks.domains.functions import solve
from bie.evaluation.benchmarks.domains.waves import solve as wave_solve
from bie.evaluation.benchmarks.versioning import Snapshot

class BatchAuditTests(Base):
    def test_reg004_policy_binding_tamper_rejected(self):
        s=self.snapshot(); ledger=AttemptLedger(self.registry)
        ledger.start(run_id='run',campaign_id='campaign',candidate_sha256='a'*64,policy_sha256='b'*64,snapshot=s,split='DEVELOPMENT')
        row=self.registry.connection.execute('SELECT binding_json FROM attempts').fetchone()
        body=strict_loads(row[0]); body['policy_sha256']='c'*64
        self.registry.connection.execute('UPDATE attempts SET binding_json=?',(canonical_json(body),))
        self.code('RUN_BINDING_TAMPERED',ledger.finalize,'run',[])
    def test_reg003_authority_repr_does_not_print_key(self):
        key=b'TEST_ONLY_SECRET_REPR_REGRESSION__'
        a=Authority('reviewer','SCIENCE_REVIEWER','test-key',key)
        self.assertNotIn(key.decode(),repr(a))
    def test_math001_float_range_rejection_is_typed(self):
        self.code('NUMERIC_REPRESENTATION_LIMIT',solve,{'op':'polynomial_value','coefficients':[1]*33,'x':1e30})
    def test_phy003_malformed_direction_is_typed(self):
        q=lambda v,u:{'value':v,'unit':u}
        data=dict(op='traveling_wave_sample',amplitude=q(1,'m'),wavelength=q(2,'m'),frequency=q(3,'Hz'),position=q(0,'m'),time=q(0,'s'),phase=q(0,'rad'),direction=[])
        self.code('INVALID_DIRECTION',wave_solve,data)
    def test_reg004_prompt_comparison_resource_bound(self):
        s=self.snapshot([case('a',1,prompt='A'*5000),case('b',2,prompt='B'*5000,split='HOLDOUT')])
        self.code('LEAKAGE_REVIEW_CAPACITY_EXCEEDED',leakage_report,s)
