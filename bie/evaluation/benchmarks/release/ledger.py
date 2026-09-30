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
        from ..storage import connect_manual
        self.db=connect_manual(p, timeout=5)
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
                             'trust_metadata':public_trust,'evaluated_at':kwargs.get('now',0),
                             'production_inputs': {k:kwargs.get(k) for k in ('candidate_bundle','assessment_tokens',
                                 'coverage_contract','expected_coverage_sha256')}})
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
                 'external_evidence_inputs_sha256':external_sha,'artifact_sha256':manifest['artifact_sha256'],'report':report}
        raw=canonical_json(receipt)
        changed = self.db.execute("UPDATE release_attempts SET state='FINAL', receipt=?, receipt_sha=? WHERE id=? AND state='RUNNING' AND inputs_sha=?",
                                  (raw,digest(receipt),attempt_id,inputs_sha)).rowcount
        if changed != 1: raise BenchmarkError('RELEASE_FINALIZE_CONFLICT')
        return self.get(attempt_id)
    def get(self,attempt_id):
        ident(attempt_id)
        row=self.db.execute('SELECT campaign, inputs_sha, state, receipt, receipt_sha, artifact FROM release_attempts WHERE id=?',(attempt_id,)).fetchone()
        if not row:raise BenchmarkError('UNKNOWN_RELEASE_ATTEMPT')
        if row[2]!='FINAL':raise BenchmarkError('RELEASE_ATTEMPT_INCOMPLETE')
        try:
            result=strict_loads(row[3])
            if digest(result)!=row[4] or result['attempt_id']!=attempt_id or result['campaign_id']!=row[0] or result['inputs_sha256']!=row[1]:
                raise BenchmarkError('RELEASE_RECEIPT_INTEGRITY')
            if result.get('artifact_sha256') is None:
                raise BenchmarkError('LEGACY_RECEIPT_REQUIRES_REVALIDATION')
            if result['artifact_sha256'] != row[5]:
                raise BenchmarkError('RELEASE_RECEIPT_ARTIFACT_MISMATCH')
            report = result['report']
            if report.get('product_accepted') is not False or report.get('release_authorized') is not False:
                raise BenchmarkError('RELEASE_RECEIPT_UNAUTHORIZED_PROMOTION')
            if 'report_sha256' in report and digest({k:v for k,v in report.items() if k!='report_sha256'}) != report['report_sha256']:
                raise BenchmarkError('RELEASE_REPORT_INTEGRITY')
            campaign=self.db.execute('SELECT binding FROM release_campaigns WHERE id=?',(row[0],)).fetchone()
            bound=strict_loads(campaign[0])
            if digest(bound)!=result['campaign_binding_sha256'] or bound['policy_sha256']!=result['policy_sha256']:
                raise BenchmarkError('RELEASE_RECEIPT_BINDING_CHANGED')
            return result
        except (KeyError,TypeError,ValueError) as exc:
            if isinstance(exc,BenchmarkError):raise
            raise BenchmarkError('RELEASE_RECEIPT_INTEGRITY') from exc

    def recover_incomplete(self, attempt_id, *, expected_inputs_sha256, operator_id, reason):
        """Privileged single-owner recovery, not a public unauthenticated API.

        Operator must first stop the abandoned worker. CAS refuses completed attempts.
        A recovered reservation is terminal BLOCKED and never yields a new attempt.
        Historical pre-H1 finalized receipts remain archived, not silently rewritten.
        """
        from .contracts import pinned
        from ..models import digest_string
        ident(attempt_id);ident(operator_id);ident(reason);digest_string(expected_inputs_sha256)
        try:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.db.execute('SELECT campaign,artifact,inputs_sha,state FROM release_attempts WHERE id=?',(attempt_id,)).fetchone()
            if row is None: raise BenchmarkError('UNKNOWN_RELEASE_ATTEMPT')
            if row[2] != expected_inputs_sha256: raise BenchmarkError('RECOVERY_INPUTS_MISMATCH')
            if row[3] != 'RUNNING': raise BenchmarkError('RECOVERY_STATE_CONFLICT')
            campaign=self.db.execute('SELECT binding FROM release_campaigns WHERE id=?',(row[0],)).fetchone()
            if campaign is None: raise BenchmarkError('RELEASE_RECEIPT_INTEGRITY')
            binding=strict_loads(campaign[0])
            receipt={'schema_version':'1.0.0','attempt_id':attempt_id,'campaign_id':row[0],
                'artifact_sha256':row[1],'inputs_sha256':row[2], 'campaign_binding_sha256':digest(binding),
                'policy_sha256':binding['policy_sha256'], 'recovery':{'operator_id':operator_id,'reason':reason},
                'report':{'outcome':'BLOCKED','reasons':['INTERRUPTED_ATTEMPT_RECOVERED'],
                    'benchmark_gate_passed':False,'release_authorized':False,'product_accepted':False}}
            changed=self.db.execute("UPDATE release_attempts SET state='FINAL',receipt=?,receipt_sha=? WHERE id=? AND state='RUNNING' AND inputs_sha=?",
                (canonical_json(receipt),digest(receipt),attempt_id,expected_inputs_sha256)).rowcount
            if changed != 1: raise BenchmarkError('RECOVERY_STATE_CONFLICT')
            self.db.execute('COMMIT')
        except BaseException:
            if self.db.in_transaction:self.db.execute('ROLLBACK')
            raise
        return self.get(attempt_id)
