"""Append-once SQLite release attempts with frozen campaign identity.

This is a single-host operator ledger, not a multi-tenant security boundary or a
signature system. A database owner can rewrite bytes and hashes; use external
signed attestations and protected storage for production integrity.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from ..models import BenchmarkError,canonical_json,digest,strict_loads,ident
from .contracts import pinned
from . import gate

class ReleaseLedger:
    def __init__(self,path):
        p=Path(path).absolute()
        for node in (p,*p.parents):
            if node.is_symlink():raise BenchmarkError('LEDGER_SYMLINK_REFUSED')
        if not p.parent.is_dir() or (p.exists() and not p.is_file()):raise BenchmarkError('INVALID_LEDGER_PATH')
        self.db=sqlite3.connect(str(p),timeout=5,isolation_level=None)
        self.db.execute('PRAGMA foreign_keys=ON');self.db.execute('PRAGMA busy_timeout=5000')
        self.db.execute('CREATE TABLE IF NOT EXISTS release_campaigns (id TEXT PRIMARY KEY, binding TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS release_attempts (id TEXT PRIMARY KEY, campaign TEXT NOT NULL REFERENCES release_campaigns(id), artifact TEXT NOT NULL, inputs_sha TEXT NOT NULL, state TEXT NOT NULL, receipt TEXT, receipt_sha TEXT, UNIQUE(campaign,artifact))')
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def close(self):self.db.close()
    def execute(self,*,campaign_id,attempt_id,manifest,policy,assessments,expected_manifest_sha256,expected_policy_sha256,**kwargs):
        ident(campaign_id);ident(attempt_id);pinned(manifest,expected_manifest_sha256);pinned(policy,expected_policy_sha256)
        # Malformed manifests cannot reserve a misleading identity.
        gate.validate_manifest(manifest)
        campaign_snapshot={k:v for k,v in manifest.items() if k not in ('artifact_sha256','cases')}
        campaign_snapshot['cases']=[{**r,'context':{k:v for k,v in r['context'].items() if k not in ('candidate_sha256','run_id')}} for r in manifest['cases']]
        binding=canonical_json({'policy_sha256':expected_policy_sha256,'suite':campaign_snapshot})
        public_trust={key:{k:v for k,v in row.items() if k!='secret'} for key,row in (kwargs.get('trust') or {}).items()}
        external_sha=digest({'attestations':kwargs.get('attestations') or [],'artifacts':kwargs.get('artifacts') or {},
                             'trust_metadata':public_trust,'evaluated_at':kwargs.get('now',0)})
        inputs_sha=digest({'manifest':manifest,'policy':policy,'assessments':assessments,'external_evidence_inputs_sha256':external_sha})
        try:
            self.db.execute('BEGIN IMMEDIATE')
            old=self.db.execute('SELECT binding FROM release_campaigns WHERE id=?',(campaign_id,)).fetchone()
            if old and old[0]!=binding:raise BenchmarkError('RELEASE_CAMPAIGN_CHANGED')
            if not old:self.db.execute('INSERT INTO release_campaigns VALUES (?,?)',(campaign_id,binding))
            self.db.execute('INSERT INTO release_attempts (id,campaign,artifact,inputs_sha,state,receipt,receipt_sha) VALUES (?,?,?,?,?,?,?)',
                            (attempt_id,campaign_id,manifest['artifact_sha256'],inputs_sha,'RUNNING',None,None))
            self.db.execute('COMMIT')
        except sqlite3.IntegrityError as exc:
            self.db.execute('ROLLBACK');raise BenchmarkError('RELEASE_ATTEMPT_ALREADY_RECORDED') from exc
        except Exception:
            if self.db.in_transaction:self.db.execute('ROLLBACK')
            raise
        try:
            report=gate.evaluate(manifest,policy,assessments,expected_manifest_sha256=expected_manifest_sha256,
                                 expected_policy_sha256=expected_policy_sha256,**kwargs)
        except BenchmarkError as exc:
            report={'outcome':'BLOCKED','reasons':[exc.code],'benchmark_gate_passed':False,'release_authorized':False,'product_accepted':False}
        except Exception as exc:
            # Keep failed attempts, but never persist secrets from exception messages.
            report={'outcome':'BLOCKED','reasons':['INTERNAL_EVALUATOR_ERROR'],'exception_type':type(exc).__name__,
                    'benchmark_gate_passed':False,'release_authorized':False,'product_accepted':False}
        receipt={'schema_version':'1.0.0','attempt_id':attempt_id,'campaign_id':campaign_id,'inputs_sha256':inputs_sha,
                 'manifest_sha256':expected_manifest_sha256,'policy_sha256':expected_policy_sha256,'campaign_binding_sha256':digest(strict_loads(binding)),
                 'external_evidence_inputs_sha256':external_sha,'report':report}
        raw=canonical_json(receipt)
        with self.db:
            self.db.execute("UPDATE release_attempts SET state='FINAL', receipt=?, receipt_sha=? WHERE id=? AND state='RUNNING'",
                            (raw,digest(receipt),attempt_id))
        return receipt
    def get(self,attempt_id):
        ident(attempt_id)
        row=self.db.execute('SELECT campaign, inputs_sha, state, receipt, receipt_sha FROM release_attempts WHERE id=?',(attempt_id,)).fetchone()
        if not row:raise BenchmarkError('UNKNOWN_RELEASE_ATTEMPT')
        if row[2]!='FINAL':raise BenchmarkError('RELEASE_ATTEMPT_INCOMPLETE')
        try:
            result=strict_loads(row[3])
            if digest(result)!=row[4] or result['attempt_id']!=attempt_id or result['campaign_id']!=row[0] or result['inputs_sha256']!=row[1]:
                raise BenchmarkError('RELEASE_RECEIPT_INTEGRITY')
            campaign=self.db.execute('SELECT binding FROM release_campaigns WHERE id=?',(row[0],)).fetchone()
            bound=strict_loads(campaign[0])
            if digest(bound)!=result['campaign_binding_sha256'] or bound['policy_sha256']!=result['policy_sha256']:
                raise BenchmarkError('RELEASE_RECEIPT_BINDING_CHANGED')
            return result
        except (KeyError,TypeError,ValueError) as exc:
            if isinstance(exc,BenchmarkError):raise
            raise BenchmarkError('RELEASE_RECEIPT_INTEGRITY') from exc
