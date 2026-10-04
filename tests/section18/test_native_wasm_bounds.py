"""Real Wasm controls under unchanged native limits; no exception/process doubles."""
from pathlib import Path
from dataclasses import asdict
import ast
import json
import os
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from test_native_bundle_cache import NativeBundleCache
from bie.compiler.linux_worker import WorkerPolicy,run_isolated


class NativeWasmBounds(NativeBundleCache):
    # Do not inherit/count the two existing cache methods a second time.
    test_default_cache_reproduces_readonly_dependency_failure=None
    test_disabled_cache_bundles_without_dependency_mutation=None

    def execute(self,source,*,flag=True,name='wasm-control.cjs'):
        script=self.project/name;script.write_text(source,encoding='utf-8')
        command=[self.node,*(['--disable-wasm-trap-handler'] if flag else []),str(script)]
        policy=WorkerPolicy()
        process,kernel=run_isolated(command,workspace=self.project,policy=policy,
                                   timeout_s=30,max_output_bytes=65536)
        self.assertEqual(kernel['resource_limits'],asdict(policy))
        self.assertEqual(kernel['resource_limits']['address_space_bytes'],8*1024**3)
        self.assertTrue(kernel['kernel_enforced'])
        self.assertTrue(kernel['no_new_privileges']);self.assertTrue(kernel['capabilities_dropped'])
        self.assertEqual(kernel['private_network'],'LOOPBACK_ONLY_NO_HOST_ROUTE')
        evidence=os.environ.get('BIE_SECTION18_WASM_EVIDENCE')
        if evidence:
            out=Path(evidence);out.mkdir(parents=True,exist_ok=True)
            target=out/(self._testMethodName+'-'+name+'.json')
            self.assertFalse(target.exists())
            target.write_text(json.dumps(dict(command=command,kernel_policy=kernel,
                process=asdict(process),node_version='22.16.0',synthetic_test=True,
                product_accepted=False),indent=2)+'\n')
        return process

    def test_unflagged_real_bundle_reproduces_wasm_startup_failure(self):
        process=self.bundle('enableCaching:false',wasm_flag=False)
        self.assertFalse(process.process.passed)
        self.assertIn('WebAssembly.Instance(): Out of memory',process.process.stderr)
        self.assertNotIn('REAL_BUNDLE_READY:',process.process.stdout)

    def test_real_out_of_bounds_module_still_traps(self):
        # Actual binary: one-page memory; exported load attempts byte65536.
        source="""const bytes=Uint8Array.from([0,97,115,109,1,0,0,0,
1,5,1,96,0,1,127,3,2,1,0,5,3,1,0,1,
7,8,1,4,108,111,97,100,0,0,10,11,1,9,0,65,128,128,4,40,2,0,11]);
const instance=new WebAssembly.Instance(new WebAssembly.Module(bytes));
try{instance.exports.load();process.exitCode=3;}
catch(error){if(!(error instanceof WebAssembly.RuntimeError))throw error;
console.log('REAL_OOB_TRAP:'+error.constructor.name);}
"""
        result=self.execute(source)
        self.assertTrue(result.process.passed,result.process.stderr)
        self.assertIn('REAL_OOB_TRAP:RuntimeError',result.process.stdout)

    def test_small_wasm_growth_and_real_os_address_limit(self):
        # Physical Wasm growth is only64KiB. The OS probe below reserves address
        # space without touching memory;8GiB must fail under the8GiB RLIMIT_AS.
        probe=self.project/'address-probe.py'
        probe.write_text("""import errno,json,mmap,resource
limits=resource.getrlimit(resource.RLIMIT_AS)
assert limits==(8589934592,8589934592),limits
try:
    mapping=mmap.mmap(-1,8589934592,flags=mmap.MAP_PRIVATE|mmap.MAP_ANONYMOUS,prot=0)
except OSError as error:
    assert error.errno==errno.ENOMEM,error
    print(json.dumps(dict(rlimit_as=list(limits),virtual_reservation_rejected=True,physical_memory_touched=False)))
else:
    mapping.close()
    raise AssertionError('OS_ADDRESS_SPACE_CEILING_NOT_ENFORCED')
""",encoding='utf-8')
        source="""const memory=new WebAssembly.Memory({initial:1,maximum:2});
if(memory.grow(1)!==1 || memory.buffer.byteLength!==131072)throw Error('growth');
let trapped=false;try{memory.grow(1);}catch(error){trapped=error instanceof RangeError;}
if(!trapped)throw Error('growth bound missing');
const {spawnSync}=require('node:child_process');
const result=spawnSync(PYTHON,['-I','/work/address-probe.py'],{encoding:'utf8',timeout:10000,maxBuffer:65536});
if(result.status!==0)throw Error('OS_PROBE_FAILED:'+result.stderr);
const receipt=JSON.parse(result.stdout);
if(receipt.rlimit_as[0]!==8589934592 || !receipt.virtual_reservation_rejected)throw Error('OS ceiling');
console.log(JSON.stringify({wasm_pages:2,growth_bound_trapped:true,...receipt}));
""".replace('PYTHON',json.dumps(sys.executable))
        result=self.execute(source)
        self.assertTrue(result.process.passed,result.process.stderr)
        data=json.loads(result.process.stdout)
        self.assertEqual(data['wasm_pages'],2);self.assertTrue(data['growth_bound_trapped'])
        self.assertEqual(data['rlimit_as'],[8*1024**3,8*1024**3])
        self.assertTrue(data['virtual_reservation_rejected']);self.assertFalse(data['physical_memory_touched'])

    def test_unrelated_node_invocations_have_no_flag_or_node_options(self):
        result=self.execute("console.log(JSON.stringify({argv:process.execArgv,options:process.env.NODE_OPTIONS||null}));",flag=False)
        self.assertTrue(result.process.passed,result.process.stderr)
        data=json.loads(result.process.stdout)
        self.assertEqual(data,dict(argv=[],options=None))
        tree=ast.parse((ROOT/'bie/compiler/real_paint.py').read_text())
        typecheck=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='isolated_typecheck')
        self.assertNotIn('--disable-wasm-trap-handler',ast.unparse(typecheck))
        self.assertNotIn('--disable-wasm-trap-handler',(ROOT/'bie/compiler/linux_worker.py').read_text())
        self.assertNotIn('NODE_OPTIONS',(ROOT/'bie/compiler/namespace_launcher.py').read_text())

    def test_actual_paint_flag_scope_is_explicit_and_receipted(self):
        tree=ast.parse((ROOT/'bie/compiler/real_paint.py').read_text())
        producer=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='produce_actual_paint')
        text=ast.unparse(producer)
        self.assertIn("'--disable-wasm-trap-handler'",text)
        self.assertIn("'command': command",text)
        self.assertIn("'/engine/bie/compiler/qa_support/remotion_raster_capture.cjs'",text)
        self.assertEqual(text.count('--disable-wasm-trap-handler'),1)
        # The real producer writes its command already. The native gate must
        # also retain that safe receipt in the uploaded TEST_RESULT on failure.
        native=ast.parse((ROOT/'tests/section18/test_native_preview_render.py').read_text())
        cls=next(n for n in native.body if isinstance(n,ast.ClassDef) and n.name=='NativePreviewRender')
        setup=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='setUpClass')
        setup_text=ast.unparse(setup)
        self.assertIn('cls.actual_paint_command_receipt',setup_text)
        self.assertIn("'actual-paint/PROCESS.json'",setup_text)
        self.assertIn('asdict(WorkerPolicy())',setup_text)
        runner=ast.parse((ROOT/'tools/run_section18_posix_validation.py').read_text())
        self.assertIn("receipt['native_actual_paint_command']",ast.unparse(runner))


if __name__=='__main__':unittest.main(verbosity=2)
