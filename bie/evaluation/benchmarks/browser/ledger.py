"""H4-009: committed attempt reservations, immutable policies, terminal readback.
Operator-owned DB directory required; hashes are not protection from its owner.
"""
from dataclasses import asdict
from ..storage import connect_manual
from ..models import BenchmarkError, canonical_json, strict_loads, digest, digest_string, ident
from .contracts import reference as validate_reference,candidate as validate_candidate,content_identity,BrowserExecutionContext
from .service import code_sha256,verify_receipt,BrowserCollectionBlocked
from .metric import evaluate

class BrowserStore:
    def __init__(self,path):
        self.db=connect_manual(path)
        self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS browser_campaigns(id TEXT PRIMARY KEY, reference_sha TEXT NOT NULL, code_sha TEXT NOT NULL, env_sha TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS browser_runs(run_id TEXT PRIMARY KEY,campaign TEXT NOT NULL, content_sha TEXT NOT NULL,
            reservation TEXT NOT NULL,reservation_sha TEXT NOT NULL,state TEXT NOT NULL,receipt TEXT,receipt_sha TEXT,
            UNIQUE(campaign,content_sha));
        ''')
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def close(self):self.db.close()
    def reserve(self,run_id,campaign_id,reference,candidate,*,expected_reference_sha256,expected_candidate_sha256,context):
        ident(run_id);ident(campaign_id)
        if type(context) is not BrowserExecutionContext:raise BenchmarkError('TRUSTED_BROWSER_CONTEXT_REQUIRED')
        context.validate();r=validate_reference(reference,limits=context.limits);c=validate_candidate(candidate,context.limits)
        if digest(r)!=digest_string(expected_reference_sha256) or digest(c)!=digest_string(expected_candidate_sha256):
            raise BenchmarkError('BROWSER_INPUT_PIN_MISMATCH')
        env=digest({'limits':asdict(context.limits),'chromium':context.chromium_sha256,
                    'allow_unsandboxed_diagnostic':context.allow_unsandboxed_diagnostic})
        rec={'run_id':run_id,'campaign_id':campaign_id,'reference_sha256':digest(r),'candidate_sha256':digest(c),
             'content_sha256':content_identity(c),'code_sha256':code_sha256(),'environment_sha256':env,'metric_id':r['metric_id']}
        self.db.execute('BEGIN IMMEDIATE')
        try:
            pins=(rec['reference_sha256'],rec['code_sha256'],env)
            existing=self.db.execute('SELECT reference_sha,code_sha,env_sha FROM browser_campaigns WHERE id=?',(campaign_id,)).fetchone()
            if existing is not None and tuple(existing)!=pins:raise BenchmarkError('BROWSER_CAMPAIGN_PIN_CHANGED')
            if self.db.execute('SELECT 1 FROM browser_runs WHERE run_id=? OR (campaign=? AND content_sha=?)',
                               (run_id,campaign_id,rec['content_sha256'])).fetchone():raise BenchmarkError('BROWSER_ATTEMPT_DUPLICATE')
            if existing is None:self.db.execute('INSERT INTO browser_campaigns VALUES(?,?,?,?)',(campaign_id,*pins))
            self.db.execute('INSERT INTO browser_runs VALUES(?,?,?,?,?,?,?,?)',
                (run_id,campaign_id,rec['content_sha256'],canonical_json(rec),digest(rec),'RUNNING',None,None))
            self.db.execute('COMMIT')
        except BaseException:self.db.execute('ROLLBACK');raise
        return rec
    def execute(self,run_id,campaign_id,reference,candidate,*,expected_reference_sha256,expected_candidate_sha256,context):
        reservation=self.reserve(run_id,campaign_id,reference,candidate,expected_reference_sha256=expected_reference_sha256,
                                 expected_candidate_sha256=expected_candidate_sha256,context=context)
        try:
            result=evaluate(reference['metric_id'],reference,candidate,
                expected_reference_sha256=expected_reference_sha256,expected_candidate_sha256=expected_candidate_sha256,
                execution_context=context)
        except BenchmarkError as exc:
            result={'status':'BLOCKED','error_code':exc.code,'reference_sha256':expected_reference_sha256,
                    'candidate_sha256':expected_candidate_sha256,'release_authorized':False,'product_accepted':False}
            if isinstance(exc,BrowserCollectionBlocked):result['browser_receipt']=exc.receipt
        except Exception as exc:
            result={'status':'BLOCKED','error_code':'BROWSER_OPERATOR_EXCEPTION','exception_type':type(exc).__name__,
                    'reference_sha256':expected_reference_sha256,'candidate_sha256':expected_candidate_sha256,
                    'release_authorized':False,'product_accepted':False}
        return self._finish(reservation,result)
    def _finish(self,reservation,result):
        rec={'schema_version':'browser-run-1','reservation':reservation,'result':result}
        self.db.execute('BEGIN IMMEDIATE')
        try:
            n=self.db.execute('UPDATE browser_runs SET state=?,receipt=?,receipt_sha=? WHERE run_id=? AND state=? AND reservation_sha=?',
                ('FINAL',canonical_json(rec),digest(rec),reservation['run_id'],'RUNNING',digest(reservation))).rowcount
            if n!=1:raise BenchmarkError('BROWSER_FINALIZATION_CONFLICT')
            self.db.execute('COMMIT')
        except BaseException:self.db.execute('ROLLBACK');raise
        return self.get(reservation['run_id'])
    def get(self,run_id):
        ident(run_id)
        row=self.db.execute('SELECT campaign,content_sha,reservation,reservation_sha,state,receipt,receipt_sha FROM browser_runs WHERE run_id=?',(run_id,)).fetchone()
        if row is None:raise BenchmarkError('BROWSER_RUN_UNKNOWN')
        if row[4]!='FINAL':raise BenchmarkError('BROWSER_RUN_NOT_FINAL')
        try:
            res=strict_loads(row[2]);rec=strict_loads(row[5]);result=rec['result']
            pins=self.db.execute('SELECT reference_sha,code_sha,env_sha FROM browser_campaigns WHERE id=?',(row[0],)).fetchone()
            if (digest(res)!=row[3] or digest(rec)!=row[6] or rec['reservation']!=res
                or res['run_id']!=run_id or res['campaign_id']!=row[0] or res['content_sha256']!=row[1]
                or tuple(pins or ())!=(res['reference_sha256'],res['code_sha256'],res['environment_sha256'])
                or result['reference_sha256']!=res['reference_sha256'] or result['candidate_sha256']!=res['candidate_sha256']
                or result.get('release_authorized') is not False or result.get('product_accepted') is not False):
                raise BenchmarkError('BROWSER_STORE_INTEGRITY')
            if result['status']=='MEASURED':
                b=verify_receipt(result['details']['browser_receipt'])
                if b['candidate_content_sha256']!=row[1] or result['evaluator_code_sha256']!=res['code_sha256']:
                    raise BenchmarkError('BROWSER_STORE_INTEGRITY')
            elif result['status']=='BLOCKED':
                if 'browser_receipt' in result:verify_receipt(result['browser_receipt'])
            else:raise BenchmarkError('BROWSER_STORE_INTEGRITY')
            return rec
        except (BenchmarkError,KeyError,TypeError,ValueError) as exc:raise BenchmarkError('BROWSER_STORE_INTEGRITY') from exc
    def recover(self,run_id,*,expected_reservation_sha256,reason):
        ident(run_id);ident(reason);digest_string(expected_reservation_sha256)
        row=self.db.execute('SELECT reservation,reservation_sha,state FROM browser_runs WHERE run_id=?',(run_id,)).fetchone()
        if row is None or row[2]!='RUNNING':raise BenchmarkError('BROWSER_RECOVERY_SCOPE')
        res=strict_loads(row[0])
        if digest(res)!=row[1] or row[1]!=expected_reservation_sha256 or res['run_id']!=run_id:raise BenchmarkError('BROWSER_RECOVERY_SCOPE')
        result={'status':'BLOCKED','error_code':'OPERATOR_RECOVERED_INTERRUPTED_RUN','operator_reason':reason,
                'reference_sha256':res['reference_sha256'],'candidate_sha256':res['candidate_sha256'],
                'release_authorized':False,'product_accepted':False}
        return self._finish(res,result)
