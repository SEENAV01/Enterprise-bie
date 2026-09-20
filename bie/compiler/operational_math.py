"""H7 kernel-isolated adoption of the existing bounded Mathtext worker.
The earlier resource-only worker remains a diagnostic API for historical tests.
"""
from functools import lru_cache
from dataclasses import asdict
from pathlib import Path
import json,sys,tempfile
from .isolated_typesetting import MathWorkerLimits
from .host_toolchain import collect_host_toolchain,validate_host_identity,CONTROLS
from .qa_common import CompilerQAError
from .linux_worker import WorkerPolicy,run_isolated

def run_operational_math(expression,element_id,font_size,expected_identity, *, limits=None):
    limits=limits or MathWorkerLimits()
    if not isinstance(expression,str) or len(expression)>2048 or not isinstance(element_id,str) or len(element_id)>512:raise CompilerQAError('MATH_INPUT_LIMIT')
    if type(font_size)is not int or not 8<=font_size<=144:raise CompilerQAError('MATH_FONT_SIZE_LIMIT')
    request={'expression':expression,'element_id':element_id,'font_size':font_size,'expected_identity':expected_identity,'limits':asdict(limits)}
    data=json.dumps(request,allow_nan=False).encode()
    if len(data)>20000:raise CompilerQAError('MATH_INPUT_LIMIT')
    engine=Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix='bie-kernel-math-') as td:
        root=Path(td);(root/'output').mkdir();(root/'input.json').write_bytes(data)
        policy=WorkerPolicy(procfs=False,cpu_seconds=limits.cpu_seconds,address_space_bytes=limits.memory_mb*1024**2,file_bytes=limits.max_output_bytes)
        p,k=run_isolated([sys.executable,'-I',str(engine/'bie/compiler/isolated_math_worker.py'),str(root/'input.json'),str(root/'output/geometry.json')],
                         workspace=root,engine=engine,writable=['output'],policy=policy,timeout_s=limits.timeout_seconds,max_output_bytes=limits.max_output_bytes)
        if not p.process.passed or not k.get('kernel_enforced'):raise CompilerQAError('MATH_OPERATIONAL_WORKER_BLOCKED:'+p.outcome+':'+p.process.stderr[:500])
        f=root/'output/geometry.json'
        if f.is_symlink() or not f.is_file() or f.stat().st_size>limits.max_output_bytes:raise CompilerQAError('MATH_OUTPUT_LIMIT')
        report=json.loads(f.read_text())
        if report.get('passed')is not True or report.get('host_identity')!=expected_identity or report.get('controlled_environment')!=CONTROLS or report.get('accepted')is not False:raise CompilerQAError('MATH_OPERATIONAL_REPORT_MISMATCH')
        report['kernel_policy']=k;report['os_security_sandbox']=True;report['scope']='LINUX_NAMESPACED_EXISTING_MATHTEXT_WORKER'
        return report

@lru_cache(maxsize=128)
def _cached(expression,element_id,font_size,identity):return json.dumps(run_operational_math(expression,element_id,font_size,identity),sort_keys=True,allow_nan=False)

def operational_typeset_latex(expression, *, element_id,font_size=32,expected_host=None):
    host=collect_host_toolchain();identity=validate_host_identity(host)
    if expected_host is not None and identity!=validate_host_identity(expected_host):raise CompilerQAError('MATH_HOST_CHANGED')
    report=json.loads(_cached(expression,element_id,font_size,identity))
    if collect_host_toolchain()['identity_sha256']!=identity:raise CompilerQAError('MATH_HOST_CHANGED')
    return report['geometry']
