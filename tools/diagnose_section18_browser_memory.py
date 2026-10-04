"""Observe early browser allocation failure without relaxing any sandbox guard.

Only a diagnostic child receives LD_PRELOAD. Real uninstrumented failure is
retained separately. This never authorizes a render/paint PASS and adds no tests.
No ptrace, new capabilities, public network, writable dependencies or larger
ceiling. The observer preserves mmap arguments/results and never repairs them.
"""
from pathlib import Path
from dataclasses import asdict
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from bie.compiler.linux_worker import WorkerPolicy,run_isolated
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert sys.platform=='linux' and not a.output.exists()
    browser=Path(os.environ['BIE_SECTION18_RENDER_BROWSER']);before=sha(browser)
    policy=WorkerPolicy();assert policy.address_space_bytes==8589934592
    compiler=shutil.which('cc');assert compiler,'diagnostic native compiler not provisioned'
    source=ROOT/'tools/section18_browser_memory_probe.c';source_sha=sha(source)
    with tempfile.TemporaryDirectory(prefix='bie-s18-allocation-probe-') as tmp:
        stage=Path(tmp);library=stage/'observer.so'
        argv=[compiler,'-std=c11','-Wall','-Wextra','-Werror','-fPIC','-shared','-O0',str(source),'-o',str(library)]
        build=subprocess.run(argv,capture_output=True,text=True,timeout=30)
        assert build.returncode==0,build.stderr
        script=stage/'observe.py'
        script.write_text('import os,sys\nenv=dict(os.environ)\nenv["LD_PRELOAD"]="/work/observer.so"\nos.execve(sys.argv[1],sys.argv[1:],env)\n')
        observations=[]
        # The unchanged /usr/bin/true control qualifies observer startup. The
        # Chrome version probe has no Remotion/Node/renderer switches at all.
        for name,command in [('observer_control',[sys.executable,'-I',str(script),'/usr/bin/true']),
                             ('browser_uninstrumented',[str(browser),'--version']),
                             ('browser_observed',[sys.executable,'-I',str(script),str(browser),'--version'])]:
            process,kernel=run_isolated(command,workspace=stage,policy=policy,timeout_s=10,max_output_bytes=64*1024)
            assert kernel['kernel_enforced'] and kernel['resource_limits']==asdict(policy)
            observations.append(dict(name=name,command=command,process=asdict(process),kernel_policy=kernel))
        control=observations[0]['process']['process']
        assert control['passed'] and 'DIAGNOSTIC_OBSERVER_LOADED_RLIMIT_AS=8589934592' in control['stderr'], 'OBSERVER_NOT_QUALIFIED'
        assert sha(browser)==before and sha(source)==source_sha
        result=dict(schema='bie.section18.browser-memory-diagnostic/1',browser_sha256=before,
                    source_sha256=source_sha,observer_sha256=sha(library),build_command=argv,
                    observations=observations,production_environment_changed=False,
                    address_space_bytes=8589934592,distinct_test_methods=0,
                    render_gate_authorized=False,actual_paint_gate_authorized=False,product_accepted=False)
        a.output.mkdir(parents=True)
        (a.output/'DIAGNOSTIC.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(dict(diagnostic_only=True,observations=[dict(name=r['name'],
            exit_code=r['process']['process']['exit_code'],stdout=r['process']['process']['stdout'],
            stderr=r['process']['process']['stderr']) for r in observations],render_gate_authorized=False)))
    return 0
if __name__=='__main__':raise SystemExit(main())
