"""H3-009: evaluator-owned transactional execution ledger.

Only execute() creates measured rows. There is no import-PASS API. The database
must be protected by the operator; hashes are not protection against its owner.
"""
from __future__ import annotations
from dataclasses import asdict
from ..models import BenchmarkError,digest,digest_string,canonical_json,strict_loads,ident,exact_fields
from ..storage import connect_manual
from ..release.contracts import context,assessment,make_assessment
from ..release.deterministic import execute as run_rater,service_code_sha256
from .contracts import METRICS,ExecutionContext,validate_reference,validate_candidate,content_identity,snapshot


def campaign(value):
    v=snapshot(value);exact_fields(v,{'schema_version','id','dataset_sha256','environment_sha256','split','cases'})
    if v['schema_version']!='av-campaign-3':raise BenchmarkError('AV_CAMPAIGN_SCHEMA')
    ident(v['id']);digest_string(v['dataset_sha256']);digest_string(v['environment_sha256'])
    if v['split'] not in ('DEVELOPMENT','CALIBRATION','HOLDOUT'):raise BenchmarkError('AV_CAMPAIGN_SPLIT')
    if type(v['cases']) is not list or not 1<=len(v['cases'])<=1000:raise BenchmarkError('AV_CAMPAIGN_CASES')
    rows={}
    for r in v['cases']:
        exact_fields(r,{'case_id','domain','metric_id','reference_sha256'})
        ident(r['case_id']);ident(r['domain']);digest_string(r['reference_sha256'])
        if r['metric_id'] not in METRICS or r['case_id'] in rows:raise BenchmarkError('AV_CAMPAIGN_CASES')
        rows[r['case_id']]=r
    return v,rows

class AdoptionStore:
    def __init__(self,path):
        self.db=connect_manual(path)
        self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS av_h3_campaigns(id TEXT PRIMARY KEY,contract_sha TEXT NOT NULL,
          contract_json TEXT NOT NULL,code_sha TEXT NOT NULL,limits_sha TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS av_h3_runs(run_id TEXT PRIMARY KEY,campaign TEXT NOT NULL,
          case_id TEXT NOT NULL,content_sha TEXT NOT NULL,context_json TEXT NOT NULL,
          code_sha TEXT NOT NULL,state TEXT NOT NULL,assessment_json TEXT,assessment_sha TEXT,
          UNIQUE(campaign,case_id,content_sha));
        """)
    def close(self):self.db.close()
    def __enter__(self):return self
    def __exit__(self,*a):self.close()
    def execute(self,contract,ctx,reference,candidate,*,expected_campaign_sha256,
                expected_code_sha256,execution_context):
        v,rows=campaign(contract);ctx=context(ctx)
        if digest(v)!=digest_string(expected_campaign_sha256):raise BenchmarkError('AV_CAMPAIGN_PIN_MISMATCH')
        if type(execution_context) is not ExecutionContext:raise BenchmarkError('TRUSTED_AV_EXECUTION_CONTEXT_REQUIRED')
        if expected_code_sha256!=service_code_sha256():raise BenchmarkError('EVALUATOR_CODE_CHANGED')
        case=rows.get(ctx['case_id'])
        if case is None or any(ctx[k]!=case[k] for k in ('case_id','domain','metric_id','reference_sha256')):
            raise BenchmarkError('AV_CASE_PIN_MISMATCH')
        if any(ctx[k]!=v[k] for k in ('dataset_sha256','environment_sha256','split')):
            raise BenchmarkError('AV_CONTEXT_CAMPAIGN_MISMATCH')
        r=validate_reference(reference,ctx['metric_id']);c=validate_candidate(candidate,ctx['metric_id'],execution_context.limits)
        if digest(r)!=ctx['reference_sha256'] or digest(c)!=ctx['candidate_sha256'] or ctx['rubric_sha256']!=digest(r):
            raise BenchmarkError('AV_INPUT_PIN_MISMATCH')
        lsha=digest(asdict(execution_context.limits))
        if r['limits_sha256']!=lsha:raise BenchmarkError('AV_LIMITS_PIN_MISMATCH')
        csha=content_identity(c);run_id=ctx['run_id']
        self.db.execute('BEGIN IMMEDIATE')
        try:
            old=self.db.execute('SELECT contract_sha,code_sha,limits_sha FROM av_h3_campaigns WHERE id=?',(v['id'],)).fetchone()
            if old is not None and tuple(old)!=(digest(v),expected_code_sha256,lsha):raise BenchmarkError('AV_CAMPAIGN_PINS_CHANGED')
            if self.db.execute('SELECT 1 FROM av_h3_runs WHERE run_id=? OR (campaign=? AND case_id=? AND content_sha=?)',
                 (run_id,v['id'],ctx['case_id'],csha)).fetchone():raise BenchmarkError('AV_ATTEMPT_ALREADY_RESERVED')
            if old is None:self.db.execute('INSERT INTO av_h3_campaigns VALUES(?,?,?,?,?)',
                (v['id'],digest(v),canonical_json(v),expected_code_sha256,lsha))
            self.db.execute('INSERT INTO av_h3_runs VALUES(?,?,?,?,?,?,?,?,?)',
                (run_id,v['id'],ctx['case_id'],csha,canonical_json(ctx),expected_code_sha256,'RUNNING',None,None))
            self.db.execute('COMMIT')
        except BaseException:self.db.execute('ROLLBACK');raise
        # The reservation is committed before any file/decoder work. A terminated
        # worker leaves RUNNING. It cannot retry itself under a different run ID.
        result=run_rater(ctx,r,c,assessor_id='av-deterministic-v3',expected_code_sha256=expected_code_sha256,
                         execution_context=execution_context)
        assessment(result,ctx)
        self._finish(run_id,result)
        return self.get(run_id)
    def _finish(self,run_id,result):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            n=self.db.execute('UPDATE av_h3_runs SET state=?,assessment_json=?,assessment_sha=? WHERE run_id=? AND state=?',
                 ('FINAL',canonical_json(result),result['assessment_sha256'],run_id,'RUNNING')).rowcount
            if n!=1:raise BenchmarkError('AV_FINALIZATION_CONFLICT')
            self.db.execute('COMMIT')
        except BaseException:self.db.execute('ROLLBACK');raise
    def get(self,run_id,*,expected_campaign_sha256=None):
        ident(run_id)
        r=self.db.execute('SELECT campaign,case_id,content_sha,context_json,code_sha,state,assessment_json,assessment_sha FROM av_h3_runs WHERE run_id=?',(run_id,)).fetchone()
        if r is None:raise BenchmarkError('AV_RUN_UNKNOWN')
        if r[5]!='FINAL':raise BenchmarkError('AV_RUN_NOT_FINAL')
        try:
            c=self.db.execute('SELECT contract_sha,contract_json,code_sha,limits_sha FROM av_h3_campaigns WHERE id=?',(r[0],)).fetchone()
            if c is None:raise BenchmarkError('AV_CAMPAIGN_MISSING')
            contract,rows=campaign(strict_loads(c[1]))
            if digest(contract)!=c[0] or contract['id']!=r[0] or r[4]!=c[2]:raise BenchmarkError('AV_CAMPAIGN_CORRUPT')
            if expected_campaign_sha256 is not None and c[0]!=digest_string(expected_campaign_sha256):raise BenchmarkError('AV_CAMPAIGN_PIN_MISMATCH')
            ctx=context(strict_loads(r[3]));a=assessment(strict_loads(r[6]),ctx);case=rows[ctx['case_id']]
            if (ctx['run_id'],ctx['case_id'])!=(run_id,r[1]) or any(ctx[k]!=case[k] for k in ('metric_id','domain','reference_sha256')):
                raise BenchmarkError('AV_CONTEXT_CORRUPT')
            if any(ctx[k]!=contract[k] for k in ('dataset_sha256','environment_sha256','split')):raise BenchmarkError('AV_CONTEXT_CORRUPT')
            if a['assessment_sha256']!=r[7] or a['kind']!='DETERMINISTIC' or a['assessor_id']!='av-deterministic-v3':
                raise BenchmarkError('AV_ASSESSMENT_CORRUPT')
            if a['evidence']['evaluator_code_sha256']!=r[4]:raise BenchmarkError('AV_CODE_PIN_CORRUPT')
            if 'av_collection' in a['evidence']:
                from ..av.service import verify_receipt
                av=verify_receipt(a['evidence']['av_collection'])
                if (av['status']!='BLOCKED' or a['status']!='BLOCKED' or digest(av)!=a['evidence']['av_collection_sha256'] or av.get('limits_sha256')!=c[3]):
                    raise BenchmarkError('AV_BLOCKED_RECORD_CORRUPT')
            if a['status']=='MEASURED':
                m=a['evidence']['metric_result']
                if (m.get('metric_profile')!='av-adoption-3' or digest(m)!=a['evidence']['metric_result_sha256']
                    or m['candidate_content_sha256']!=r[2] or m['evaluator_code_sha256']!=r[4]
                    or m['reference_sha256']!=ctx['reference_sha256'] or m['candidate_sha256']!=ctx['candidate_sha256']
                    or m['details']['av_receipt']['limits_sha256']!=c[3]):raise BenchmarkError('AV_METRIC_RECORD_CORRUPT')
                from ..av.service import verify_receipt
                verify_receipt(m['details']['av_receipt'])
            return a
        except (BenchmarkError,KeyError,TypeError,ValueError) as exc:raise BenchmarkError('AV_STORE_INTEGRITY') from exc
    def recover(self,run_id,*,expected_context_sha256,operator_reason):
        ident(run_id);ident(operator_reason);digest_string(expected_context_sha256)
        row=self.db.execute('SELECT context_json,code_sha,state FROM av_h3_runs WHERE run_id=?',(run_id,)).fetchone()
        if row is None or row[2]!='RUNNING':raise BenchmarkError('AV_RECOVERY_SCOPE_MISMATCH')
        ctx=context(strict_loads(row[0]))
        if digest(ctx)!=expected_context_sha256:raise BenchmarkError('AV_RECOVERY_SCOPE_MISMATCH')
        result=make_assessment(ctx,'av-deterministic-v3','DETERMINISTIC',0,status='BLOCKED',
             reasons=['OPERATOR_RECOVERED_ABANDONED_RUN',operator_reason],evidence={'evaluator_code_sha256':row[1]})
        self._finish(run_id,result);return self.get(run_id)
