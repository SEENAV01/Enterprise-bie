"""Bounded genuine browser launch diagnostic under unchanged compiler policy.

No production runner override; this diagnostic never authorizes paint/render PASS.
No source content, credentials, host environment or public network is exposed.
"""
from pathlib import Path
from dataclasses import asdict
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from bie.compiler.linux_worker import WorkerPolicy,run_isolated
from bie.compiler.installed_toolchain import collect_installed_toolchain,require_same_toolchain

SCRIPT=r'''const cp=require('node:child_process');
const real=cp.spawn;
cp.spawn=function(executable,args,options){
  console.log('OBSERVED_BROWSER_ARGV:'+JSON.stringify([executable,...args]));
  const child=real.call(this,executable,args,options);
  child.on('exit',(code,signal)=>console.log('OBSERVED_BROWSER_EXIT:'+JSON.stringify({code,signal})));
  child.on('error',error=>console.log('OBSERVED_BROWSER_SPAWN_ERROR:'+error.code));
  return child;
};
const {openBrowser}=require('@remotion/renderer');
openBrowser('chrome',{browserExecutable:process.argv[2],logLevel:'verbose',
  chromiumOptions:{enableMultiProcessOnLinux:true}})
 .then(async browser=>{console.log('GENUINE_BROWSER_OPENED');await browser.close({silent:true});})
 .catch(error=>{console.error(String(error));process.exitCode=2;});
'''
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    assert sys.platform=='linux'
    prepared=Path(os.environ['BIE_SECTION18_RENDER_PROJECT'])
    browser=os.environ['BIE_SECTION18_RENDER_BROWSER'];node=shutil.which('node')
    assert subprocess.check_output([node,'--version'],text=True).strip()=='v22.16.0'
    policy=WorkerPolicy();assert policy.address_space_bytes==8589934592
    assert not args.output.exists();args.output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='bie-s18-browser-diagnostic-') as tmp:
        stage=Path(tmp)/'project'
        shutil.copytree(prepared,stage,symlinks=True,
                        ignore=shutil.ignore_patterns('out','render-evidence','validation-runs'))
        before=collect_installed_toolchain(stage,node=node,browser=browser)
        script=stage/'diagnostic.cjs';script.write_text(SCRIPT,encoding='utf-8')
        command=[node,'--disable-wasm-trap-handler',str(script),browser]
        process,kernel=run_isolated(command,workspace=stage,policy=policy,timeout_s=45,max_output_bytes=1024*1024)
        require_same_toolchain(before,collect_installed_toolchain(stage,node=node,browser=browser))
        assert kernel['kernel_enforced'] and kernel['resource_limits']==asdict(policy)
        receipt=dict(schema='bie.section18.native-browser-diagnostic/1',command=command,
            process=asdict(process),kernel_policy=kernel,toolchain_identity=before,
            dependencies_unchanged=True,cache_created=(stage/'node_modules/.cache').exists(),
            source='SYNTHETIC_TEST',distinct_test_methods=0,render_gate_authorized=False,
            actual_paint_gate_authorized=False,product_accepted=False)
        assert receipt['cache_created'] is False
        (args.output/'DIAGNOSTIC.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps(dict(diagnostic_only=True,browser_opened='GENUINE_BROWSER_OPENED' in process.process.stdout,
                             stdout=process.process.stdout,stderr=process.process.stderr,
                             outcome=process.outcome,render_gate_authorized=False)))
    # Successful evidence COLLECTION is not a successful native-render gate.
    return 0
if __name__=='__main__':raise SystemExit(main())
