"""Local append-only metric run receipts and campaign reference pinning.

SQLite/file custody and external anchoring are deployment responsibilities.
A receipt hash detects accidental/uncoordinated mutation, not an adversary who
can replace both the receipt and its hash inside the evaluator database.
"""
from __future__ import annotations
from pathlib import Path
import sqlite3
from ..models import BenchmarkError,canonical_json,digest,digest_string,ident,strict_loads
from . import evaluate,evaluator_code_sha256

class MetricRunStore:
    def __init__(self,path):
        # Use a caller-controlled, trusted directory. This preflight rejects
        # existing symlinks/nonregular paths; it is not a race-proof filesystem
        # sandbox against another process with write access to that directory.
        if str(path) != ':memory:':
            target=Path(path)
            checks=[target,*target.parents,Path(str(target)+'-wal'),Path(str(target)+'-shm')]
            if any(p.is_symlink() for p in checks) or (target.exists() and not target.is_file()):
                raise BenchmarkError('DATABASE_PATH_NOT_REGULAR')
        self.db=sqlite3.connect(str(path),timeout=10,isolation_level=None)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS metric_campaigns(
          campaign TEXT NOT NULL, metric TEXT NOT NULL, reference_sha TEXT NOT NULL,
          code_sha TEXT NOT NULL, PRIMARY KEY(campaign,metric));
        CREATE TABLE IF NOT EXISTS metric_runs(
          run_id TEXT PRIMARY KEY, campaign TEXT NOT NULL, metric TEXT NOT NULL,
          candidate_sha TEXT NOT NULL, reference_sha TEXT NOT NULL,
          receipt TEXT NOT NULL, receipt_sha TEXT NOT NULL,
          UNIQUE(campaign,metric,candidate_sha),
          FOREIGN KEY(campaign,metric) REFERENCES metric_campaigns(campaign,metric));
        """)
    def close(self):self.db.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def execute(self,*,run_id,campaign_id,metric_id,reference,candidate,expected_reference_sha256,
                expected_candidate_sha256,source_artifacts=None,evaluator_id='bie-metric-evaluator-v1'):
        for v in (run_id,campaign_id,metric_id,evaluator_id):ident(v)
        rsha=digest_string(expected_reference_sha256);csha=digest_string(expected_candidate_sha256)
        # Bind actual serialized submissions before the attempt is recorded.
        if digest(reference)!=rsha:raise BenchmarkError('REFERENCE_SNAPSHOT_MISMATCH')
        if digest(candidate)!=csha:raise BenchmarkError('CANDIDATE_SNAPSHOT_MISMATCH')
        code=evaluator_code_sha256();self.db.execute('BEGIN IMMEDIATE')
        try:
            policy=self.db.execute('SELECT reference_sha,code_sha FROM metric_campaigns WHERE campaign=? AND metric=?',(campaign_id,metric_id)).fetchone()
            if policy is not None and policy!=(rsha,code):raise BenchmarkError('CAMPAIGN_REFERENCE_OR_CODE_CHANGED')
            if self.db.execute('SELECT 1 FROM metric_runs WHERE run_id=? OR (campaign=? AND metric=? AND candidate_sha=?)',(run_id,campaign_id,metric_id,csha)).fetchone():
                raise BenchmarkError('METRIC_ATTEMPT_ALREADY_RECORDED')
            if policy is None:self.db.execute('INSERT INTO metric_campaigns VALUES(?,?,?,?)',(campaign_id,metric_id,rsha,code))
            try:
                report=evaluate(metric_id,reference,candidate,expected_reference_sha256=rsha,
                    expected_candidate_sha256=csha,source_artifacts=source_artifacts,evaluator_id=evaluator_id)
            except BenchmarkError as exc:
                # Persist a blocked attempt rather than making evidence failures
                # disappear from the campaign. It receives no numeric score.
                report={'schema_version':'1.0.0','metric_id':metric_id,'status':'BLOCKED','error_code':exc.code,
                        'reference_sha256':rsha,'candidate_sha256':csha,'evaluator_code_sha256':code,
                        'evaluator_id':evaluator_id,'release_authorized':False,'product_accepted':False}
            receipt={'run_id':run_id,'campaign_id':campaign_id,'report':report}
            self.db.execute('INSERT INTO metric_runs VALUES(?,?,?,?,?,?,?)',
                (run_id,campaign_id,metric_id,csha,rsha,canonical_json(receipt),digest(receipt)))
            self.db.execute('COMMIT');return receipt
        except BaseException:
            self.db.execute('ROLLBACK');raise
    def get(self,run_id):
        ident(run_id)
        row=self.db.execute('SELECT campaign,metric,candidate_sha,reference_sha,receipt,receipt_sha FROM metric_runs WHERE run_id=?',(run_id,)).fetchone()
        if row is None:raise BenchmarkError('UNKNOWN_METRIC_RUN')
        try:
            receipt=strict_loads(row[4])
        except BenchmarkError as exc:
            raise BenchmarkError('METRIC_RECEIPT_INTEGRITY_FAILURE') from exc
        if type(receipt) is not dict or type(receipt.get('report')) is not dict:
            raise BenchmarkError('METRIC_RECEIPT_INTEGRITY_FAILURE')
        report=receipt['report']
        if digest(receipt)!=row[5] or receipt.get('run_id')!=run_id or receipt.get('campaign_id')!=row[0] or report.get('metric_id')!=row[1] or report.get('candidate_sha256')!=row[2] or report.get('reference_sha256')!=row[3]:
            raise BenchmarkError('METRIC_RECEIPT_INTEGRITY_FAILURE')
        return receipt
