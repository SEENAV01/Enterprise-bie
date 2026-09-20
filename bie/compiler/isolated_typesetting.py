"""H3-004 isolated compile-time Mathtext adapter with identity-aware immutable cache."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from functools import lru_cache
from pathlib import Path
import json,os,signal,subprocess,sys,tempfile,math
from .qa_common import CompilerQAError, digest
from .hardening_contracts import reject
from .host_toolchain import CONTROLS,collect_host_toolchain,validate_host_identity

@dataclass(frozen=True)
class MathWorkerLimits:
    timeout_seconds: float = 30.
    cpu_seconds: int = 15
    memory_mb: int = 2048
    max_output_bytes: int = 2*1024*1024
    def __post_init__(self):
        v=self.timeout_seconds
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not .001<=v<=60:
            raise CompilerQAError('MATH_LIMIT_INVALID: wall time')
        for k,lo,hi in [('cpu_seconds',1,30),('memory_mb',256,4096),('max_output_bytes',1024,8*1024*1024)]:
            if type(getattr(self,k)) is not int or not lo<=getattr(self,k)<=hi:
                raise CompilerQAError('MATH_LIMIT_INVALID: '+k)


def run_math_worker(expression,element_id,font_size,expected_identity,*,limits=None):
    limits=limits or MathWorkerLimits()
    if os.name!='posix':reject('MATH_WORKER_PLATFORM_UNSUPPORTED','requires a governed POSIX resource adapter')
    if not isinstance(expression,str) or len(expression)>2048 or not isinstance(element_id,str) or len(element_id)>512:
        reject('MATH_INPUT_LIMIT','bounded text input required')
    from .artifact_hashing import require_sha256
    require_sha256(expected_identity)
    request={'expression':expression,'element_id':element_id,'font_size':font_size,
             'expected_identity':expected_identity,'limits':asdict(limits)}
    data=json.dumps(request,allow_nan=False).encode()
    if len(data)>20000:reject('MATH_INPUT_LIMIT','request exceeds byte budget')
    worker=Path(__file__).with_name('isolated_math_worker.py').resolve()
    with tempfile.TemporaryDirectory(prefix='bie-math-h3-') as td:
        root=Path(td);inp=root/'input.json';out=root/'output.json';err=root/'worker.stderr'
        inp.write_bytes(data)
        env={**CONTROLS,'PATH':'/usr/bin:/bin','HOME':str(root),'MPLCONFIGDIR':str(root/'mpl'),
             'XDG_CACHE_HOME':str(root/'cache'),'TMPDIR':str(root)}
        with err.open('wb') as log:
            process=subprocess.Popen([sys.executable,'-I',str(worker),str(inp),str(out)],cwd=root,env=env,
                       stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=log,start_new_session=True)
            try:
                try:code=process.wait(timeout=limits.timeout_seconds)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=3)
                    reject('MATH_WORKER_TIMEOUT','typesetter exceeded its wall budget')
            finally:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                if process.poll() is None:process.wait(timeout=3)
        if not out.is_file() or out.is_symlink():
            reject('MATH_WORKER_FAILED','child did not publish output; exit='+str(code))
        if out.stat().st_size>limits.max_output_bytes:reject('MATH_OUTPUT_LIMIT','child output too large')
        report=json.loads(out.read_text())
        if report.get('passed') is not True or code!=0:
            text=report.get('error','unknown worker error')
            if text=='MATH_WORKER_HOST_MISMATCH':reject(text,'toolchain identity changed before child execution')
            reject('MATH_WORKER_REJECTED',str(text))
        if report.get('host_identity')!=expected_identity or report.get('execution_kind')!='REAL_ISOLATED_PYTHON_MATHTEXT' or report.get('accepted') is not False:
            reject('MATH_WORKER_RECEIPT_INVALID','child identity/scope mismatch')
        if report.get('controlled_environment')!=CONTROLS:reject('MATH_WORKER_ENVIRONMENT_INVALID','controls differ')
        expected_limits={'RLIMIT_CPU':[limits.cpu_seconds]*2,'RLIMIT_AS':[limits.memory_mb*1024*1024]*2,
                         'RLIMIT_FSIZE':[limits.max_output_bytes]*2,'RLIMIT_NOFILE':[128,128],'RLIMIT_CORE':[0,0]}
        if report.get('observed_limits')!=expected_limits:reject('MATH_WORKER_LIMITS_INVALID','actual resource limits differ')
        return report


@lru_cache(maxsize=128)
def _isolated_cache(expression,element_id,font_size,identity):
    # Canonical JSON prevents callers mutating shared cached trees. Identity is in
    # the key, unlike the historical in-process expression-only Mathtext cache.
    return json.dumps(run_math_worker(expression,element_id,font_size,identity),sort_keys=True,allow_nan=False)


def isolated_typeset_latex(expression,*,element_id,font_size=32,expected_host=None):
    host=collect_host_toolchain()
    identity=validate_host_identity(host)
    if expected_host is not None and identity!=validate_host_identity(expected_host):
        reject('MATH_HOST_CHANGED','recompile under a new governed host identity')
    report=json.loads(_isolated_cache(expression,element_id,font_size,identity))
    # Confirm currently observed inputs still match even on a cache hit.
    if collect_host_toolchain()['identity_sha256']!=identity:
        reject('MATH_HOST_CHANGED','host inputs changed while producing geometry')
    return report['geometry']
