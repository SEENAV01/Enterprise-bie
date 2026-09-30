"""H2-010: durable attempt reservations and pin-checked AV receipt retrieval.

Single-host evaluator-owned SQLite, not multi-tenant authentication or off-host
anchoring. Operator recovery requires the abandoned worker to be stopped first.
"""
from __future__ import annotations
from dataclasses import asdict
import sqlite3
from ..models import BenchmarkError,canonical_json,digest,digest_string,strict_loads,ident
from ..storage import connect_manual
from .service import collect_and_evaluate,code_sha256,validate_policy,verify_receipt
from .custody import Limits

class AVRunStore:
    def __init__(self,path):
        self.db=connect_manual(path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS av_h2_campaigns(campaign TEXT PRIMARY KEY, policy_sha TEXT NOT NULL,code_sha TEXT NOT NULL,limits_sha TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS av_h2_runs(run_id TEXT PRIMARY KEY,campaign TEXT NOT NULL,candidate_sha TEXT NOT NULL,policy_sha TEXT NOT NULL,
        code_sha TEXT NOT NULL,state TEXT NOT NULL,receipt TEXT,receipt_sha TEXT,UNIQUE(campaign,candidate_sha));
        ''')
    def close(self):self.db.close()
    def __enter__(self):return self
    def __exit__(self,*a):self.close()
    def execute(self,*,campaign_id,run_id,media_path,media_sha256,policy,policy_sha256,
                caption_path=None,caption_sha256=None,caption_format='srt',limits=Limits()):
        ident(campaign_id);ident(run_id);digest_string(media_sha256);digest_string(policy_sha256)
        p=validate_policy(policy)
        if digest(p)!=policy_sha256:raise BenchmarkError('REFERENCE_POLICY_HASH_MISMATCH')
        if (caption_path is None)!=(caption_sha256 is None):raise BenchmarkError('CAPTION_HASH_REQUIRED')
        if caption_sha256 is not None:digest_string(caption_sha256)
        if caption_format not in ('srt','vtt'):raise BenchmarkError('UNSUPPORTED_CAPTION_FORMAT')
        candidate={'media_sha256':media_sha256,'caption_sha256':caption_sha256,'caption_format':caption_format if caption_path is not None else None}
        csha=digest(candidate);code=code_sha256();lsha=digest(asdict(limits))
        self.db.execute('BEGIN IMMEDIATE')
        try:
            old=self.db.execute('SELECT policy_sha,code_sha,limits_sha FROM av_h2_campaigns WHERE campaign=?',(campaign_id,)).fetchone()
            if old is not None and tuple(old)!=(policy_sha256,code,lsha):raise BenchmarkError('AV_CAMPAIGN_PINS_CHANGED')
            if self.db.execute('SELECT 1 FROM av_h2_runs WHERE run_id=? OR (campaign=? AND candidate_sha=?)',(run_id,campaign_id,csha)).fetchone():
                raise BenchmarkError('AV_ATTEMPT_ALREADY_RESERVED')
            if old is None:self.db.execute('INSERT INTO av_h2_campaigns VALUES(?,?,?,?)',(campaign_id,policy_sha256,code,lsha))
            self.db.execute('INSERT INTO av_h2_runs VALUES(?,?,?,?,?,?,?,?)',(run_id,campaign_id,csha,policy_sha256,code,'RUNNING',None,None))
            self.db.execute('COMMIT')
        except BaseException:self.db.execute('ROLLBACK');raise
        # A crash here leaves RUNNING: explicit terminal recovery, never silent retry.
        report=collect_and_evaluate(media_path=media_path,media_sha256=media_sha256,policy=p,policy_sha256=policy_sha256,
            run_id=run_id,caption_path=caption_path,caption_sha256=caption_sha256,caption_format=caption_format,limits=limits)
        verify_receipt(report)
        if (report['candidate_sha256'],report['reference_sha256'],report['evaluator_code_sha256'])!=(csha,policy_sha256,code):raise BenchmarkError('AV_RESULT_PIN_CHANGED')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            n=self.db.execute('UPDATE av_h2_runs SET state=?,receipt=?,receipt_sha=? WHERE run_id=? AND state=?',
                ('FINAL',canonical_json(report),digest(report),run_id,'RUNNING')).rowcount
            if n!=1:raise BenchmarkError('AV_FINALIZATION_CONFLICT')
            self.db.execute('COMMIT')
        except BaseException:self.db.execute('ROLLBACK');raise
        return self.get(run_id)
    def get(self,run_id):
        ident(run_id)
        row=self.db.execute('SELECT candidate_sha,policy_sha,code_sha,state,receipt,receipt_sha FROM av_h2_runs WHERE run_id=?',(run_id,)).fetchone()
        if row is None:raise BenchmarkError('AV_RUN_UNKNOWN')
        if row[3]!='FINAL':raise BenchmarkError('AV_RUN_NOT_FINAL')
        try:
            r=strict_loads(row[4]);verify_receipt(r)
            if digest(r)!=row[5] or (r['run_id'],r['candidate_sha256'],r['reference_sha256'],r['evaluator_code_sha256'])!=(run_id,row[0],row[1],row[2]):raise BenchmarkError('AV_STORE_INTEGRITY')
            return r
        except (BenchmarkError,TypeError,KeyError) as e:raise BenchmarkError('AV_STORE_INTEGRITY') from e
    def recover(self,run_id,*,candidate_sha256,policy_sha256,operator_reason):
        ident(run_id);digest_string(candidate_sha256);digest_string(policy_sha256);ident(operator_reason)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row=self.db.execute('SELECT candidate_sha,policy_sha,code_sha,state FROM av_h2_runs WHERE run_id=?',(run_id,)).fetchone()
            if row is None or row[3]!='RUNNING' or tuple(row[:2])!=(candidate_sha256,policy_sha256):raise BenchmarkError('AV_RECOVERY_SCOPE_MISMATCH')
            # A reserved candidate digest is retained; no content fabricated for recovery.
            r={'schema_version':'av-result-2','run_id':run_id,'candidate_sha256':candidate_sha256,'candidate_identity':None,
               'reference_sha256':policy_sha256,'evaluator_code_sha256':row[2],'status':'BLOCKED','reasons':['OPERATOR_RECOVERED_ABANDONED_RUN',operator_reason],
               'release_authorized':False,'product_accepted':False,'native_execution_verified':False,'observations':None,'recovery':True}
            r['receipt_sha256']=digest(r)
            n=self.db.execute('UPDATE av_h2_runs SET state=?,receipt=?,receipt_sha=? WHERE run_id=? AND state=?',('FINAL',canonical_json(r),digest(r),run_id,'RUNNING')).rowcount
            if n!=1:raise BenchmarkError('AV_FINALIZATION_CONFLICT')
            self.db.execute('COMMIT')
        except BaseException:self.db.execute('ROLLBACK');raise
        return self.get(run_id)
