"""Bound actual browser execution to assets/reference/tool/code; retain negatives."""
from dataclasses import asdict
from pathlib import Path
import hashlib,sys,tempfile,base64
from ..models import BenchmarkError,digest,canonical_json,strict_loads
from ..av.process import capture,Deadline
from .contracts import BrowserExecutionContext,reference,candidate,content_identity
from .bundle import freeze

class BrowserCollectionBlocked(BenchmarkError):
    def __init__(self,receipt):
        self.receipt=receipt;super().__init__('BROWSER_COLLECTION_BLOCKED')

def binary_hash(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file():raise BenchmarkError('BROWSER_EXECUTABLE_UNSAFE')
    with p.open('rb') as stream:
        if stream.read(4)!=b'\x7fELF':raise BenchmarkError('BROWSER_EXECUTABLE_NOT_NATIVE_BINARY')
        stream.seek(0);return hashlib.file_digest(stream,'sha256').hexdigest()

def code_sha256():
    from ..release.deterministic import service_code_sha256
    return service_code_sha256()

def verify_receipt(receipt):
    if type(receipt) is not dict:raise BenchmarkError('BROWSER_RECEIPT_INTEGRITY')
    core={k:v for k,v in receipt.items() if k!='receipt_sha256'}
    if receipt.get('receipt_sha256')!=digest(core):raise BenchmarkError('BROWSER_RECEIPT_INTEGRITY')
    if receipt.get('status') not in ('COLLECTED','BLOCKED') or receipt.get('product_accepted') is not False:
        raise BenchmarkError('BROWSER_RECEIPT_INTEGRITY')
    if receipt['status']=='COLLECTED':
        for run in receipt['observed']['runs']:
            shot=run['screenshot']
            try:raw=base64.b64decode(shot['png_base64'],validate=True)
            except (ValueError,TypeError) as exc:raise BenchmarkError('BROWSER_SCREENSHOT_INTEGRITY') from exc
            if len(raw)!=shot['size_bytes'] or hashlib.sha256(raw).hexdigest()!=shot['sha256'] or not raw.startswith(b'\x89PNG\r\n\x1a\n'):
                raise BenchmarkError('BROWSER_SCREENSHOT_INTEGRITY')
    if receipt['status']=='COLLECTED' and receipt.get('observed',{}).get('transport')=='REAL_LOOPBACK_HTTP_MODULE_APP':
        from .served.evidence import validate
        try:validate(receipt['http_contract']['reference'],receipt['http_contract']['candidate'],receipt['observed'])
        except BenchmarkError:raise
        except (KeyError,TypeError,ValueError) as exc:raise BenchmarkError('HTTP_RECEIPT_BINDING_MISSING') from exc
    return receipt

def execute(reference_value,candidate_value,context):
    if type(context) is not BrowserExecutionContext:raise BenchmarkError('TRUSTED_BROWSER_CONTEXT_REQUIRED')
    context.validate();limits=context.limits
    r=reference(reference_value,limits=limits);c=candidate(candidate_value,limits)
    code=code_sha256()
    rec={'schema_version':'browser-collection-1','status':'BLOCKED','reference_sha256':digest(r),
        'candidate_sha256':digest(c),'candidate_content_sha256':content_identity(c),
        'limits_sha256':digest(asdict(limits)),'evaluator_code_sha256':code,
        'chromium_sha256':context.chromium_sha256,'product_accepted':False,
        'release_authorized':False,'native_bie_execution_verified':False,
        'learner_improvement_verified':False,'independently_reviewed':False}
    try:
        http_mode=r['schema_version']=='browser-http-reference-1'
        if http_mode:
            from .served.contracts import binding
            binding(r,c)
            if c['origin_kind']!='AUTHORED_FIXTURE':raise BenchmarkError('HTTP_NONAUTHORED_RUNTIME_NOT_ADMITTED')
            rec['http_contract']={'reference':r,'candidate':c}
        elif c['load_mode']=='HTTP_MODULE_APP':raise BenchmarkError('HTTP_REFERENCE_PROFILE_REQUIRED')
        if binary_hash(context.chromium_executable)!=context.chromium_sha256:raise BenchmarkError('BROWSER_TOOL_PIN_MISMATCH')
        deadline=Deadline(limits.total_timeout_seconds)
        with freeze(context.artifact_root,c,limits) as (root,custody),tempfile.TemporaryDirectory(prefix='bie-browser-worker-') as tmp:
            config={'reference':r,'candidate':c,'snapshot_root':str(root),'limits':asdict(limits),
                    'chromium_executable':context.chromium_executable,
                    'allow_unsandboxed_diagnostic':context.allow_unsandboxed_diagnostic}
            p=Path(tmp)/'config.json';p.write_text(canonical_json(config),encoding='utf-8')
            worker=Path(__file__).parent/'served/worker.py' if http_mode else Path(__file__).with_name('worker.py')
            raw,proc=capture([str(Path(sys.executable).resolve()),str(worker),str(p)],
                             tmp,deadline,limit=limits.max_receipt_bytes)
            observed=strict_loads(raw.decode('utf-8'))
            rec['process']={k:v for k,v in proc.items() if k!='argv'};rec['custody']=custody
            if observed.get('status')!='COLLECTED':
                rec['error_code']=observed.get('error_code','BROWSER_COLLECTION_INCOMPLETE');rec['worker_error']=observed
            else:
                if len(observed.get('runs',[]))!=r['replay_count']:raise BenchmarkError('BROWSER_REPLAY_INCOMPLETE')
                if binary_hash(context.chromium_executable)!=context.chromium_sha256:raise BenchmarkError('BROWSER_TOOL_CHANGED_DURING_RUN')
                if code_sha256()!=code:raise BenchmarkError('BROWSER_CODE_CHANGED_DURING_RUN')
                if http_mode:
                    from .served.evidence import validate
                    validate(r,c,observed)
                rec['status']='COLLECTED';rec['observed']=observed
    except BenchmarkError as exc:rec['error_code']=exc.code
    except (OSError,UnicodeError,ValueError) as exc:rec['error_code']='BROWSER_COLLECTION_ERROR';rec['exception_type']=type(exc).__name__
    rec['receipt_sha256']=digest(rec);verify_receipt(rec);return rec
