"""Trusted executable for one bounded H3 math request; no caller code is loaded."""
from __future__ import annotations
from pathlib import Path
import json,os,sys
# -I ignores PYTHONPATH; this is the exact packaged compiler tree, not caller cwd.
APP=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(APP))


def main():
    import resource
    request_path,out_path=map(Path,sys.argv[1:3])
    if request_path.stat().st_size>20000:raise ValueError('MATH_INPUT_LIMIT')
    req=json.loads(request_path.read_text())
    limits=req['limits']
    resource.setrlimit(resource.RLIMIT_CPU,(limits['cpu_seconds'],limits['cpu_seconds']))
    resource.setrlimit(resource.RLIMIT_AS,(limits['memory_mb']*1024*1024,limits['memory_mb']*1024*1024))
    resource.setrlimit(resource.RLIMIT_FSIZE,(limits['max_output_bytes'],limits['max_output_bytes']))
    resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    from bie.compiler.host_toolchain import collect_host_toolchain,CONTROLS
    from bie.compiler.equation_typesetting import typeset_latex
    from bie.compiler.qa_common import diagnostic_message
    try:
        host=collect_host_toolchain()
        if host['identity_sha256']!=req['expected_identity']:
            raise ValueError('MATH_WORKER_HOST_MISMATCH')
        geometry=typeset_latex(req['expression'],element_id=req['element_id'],font_size=req['font_size'])
        report={'passed':True,'geometry':geometry,'host_identity':host['identity_sha256'],
                'execution_kind':'REAL_ISOLATED_PYTHON_MATHTEXT','resource_limits':limits,
                'observed_limits':{name:list(resource.getrlimit(getattr(resource,name))) for name in ('RLIMIT_CPU','RLIMIT_AS','RLIMIT_FSIZE','RLIMIT_NOFILE','RLIMIT_CORE')},
                'process_isolation':True,'os_security_sandbox':False,
                'controlled_environment':{k:os.environ.get(k) for k in CONTROLS},'accepted':False}
    except Exception as exc:
        report={'passed':False,'error':diagnostic_message(exc)[:4000],
                'execution_kind':'REAL_ISOLATED_PYTHON_MATHTEXT','accepted':False}
    data=json.dumps(report,sort_keys=True,allow_nan=False).encode()
    if len(data)>limits['max_output_bytes']:raise ValueError('MATH_OUTPUT_LIMIT')
    with out_path.open('xb') as f:f.write(data)
    return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
