"""Compare existing pinned full/headless builds under the unchanged worker.

This is evidence collection only (zero test methods), never a render waiver.
No browser/security-disabling switch, replacement allocator, new dependency,
policy widening or production browser selection is made. The original browser
and all existing installed toolchain files remain unchanged.
"""
from pathlib import Path
from dataclasses import asdict
import argparse,hashlib,importlib.metadata,json,os,shutil,subprocess,sys,tempfile
import playwright
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from bie.compiler.linux_worker import WorkerPolicy,run_isolated

DEST=Path('/usr/local/lib/bie-section18-headless-shell')
EXPECTED_VERSION='143.0.7499.4'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inventory(root):
    rows=[]
    for file in sorted(root.rglob('*')):
        relative=file.relative_to(root).as_posix()
        if file.is_symlink():
            assert file.resolve().is_relative_to(root.resolve()),'EXTERNAL_BROWSER_SYMLINK'
            rows.append(dict(path=relative,symlink=os.readlink(file)))
        elif file.is_file():rows.append(dict(path=relative,bytes=file.stat().st_size,sha256=sha(file)))
    assert rows
    return rows

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    assert sys.platform=='linux' and not args.output.exists() and not DEST.exists()
    assert importlib.metadata.version('playwright')=='1.57.0'
    metadata=Path(playwright.__file__).resolve().parent/'driver/package/browsers.json'
    registry=json.loads(metadata.read_text())
    pins={row['name']:row for row in registry['browsers']}
    for name in ('chromium','chromium-headless-shell'):
        assert pins[name]['revision']=='1200' and pins[name]['browserVersion']==EXPECTED_VERSION
    with sync_playwright() as p:full=Path(p.chromium.executable_path)
    # The existing default install has both pinned builds. Search only the
    # registry-derived headless revision, not arbitrary folders or user data.
    installed=next(parent for parent in full.parents if parent.name=='chromium-1200').parent
    headless_root=installed/'chromium_headless_shell-1200'
    assert headless_root.is_dir() and not headless_root.is_symlink()
    binaries=[p for p in headless_root.rglob('*') if p.name in ('headless_shell','chrome-headless-shell') and p.is_file()]
    assert len(binaries)==1,'PINNED_HEADLESS_BINARY_NOT_UNIQUE'
    original=binaries[0];source=original.parent
    assert original.read_bytes()[:4]==b'\x7fELF' and not original.is_symlink()
    headless_before=inventory(source);full_before=sha(full)
    copy=['sudo','-n','cp','-a','--',str(source),str(DEST)]
    subprocess.run(copy,check=True,timeout=60,capture_output=True)
    assert inventory(DEST)==headless_before
    headless=DEST/original.name
    policy=WorkerPolicy();assert policy.address_space_bytes==8589934592
    compiler=shutil.which('cc');assert compiler
    probe=ROOT/'tools/section18_browser_memory_probe.c';probe_before=sha(probe)
    with tempfile.TemporaryDirectory(prefix='bie-s18-browser-compatibility-') as tmp:
        stage=Path(tmp);observer=stage/'observer.so'
        build=[compiler,'-std=c11','-Wall','-Wextra','-Werror','-fPIC','-shared','-O0',str(probe),'-o',str(observer)]
        subprocess.run(build,check=True,capture_output=True,timeout=30)
        script=stage/'observe.py'
        script.write_text('import os,sys\nenv=dict(os.environ)\nenv["LD_PRELOAD"]="/work/observer.so"\nos.execve(sys.argv[1],sys.argv[1:],env)\n')
        observations=[]
        full_sandbox=Path(os.environ['BIE_SECTION18_RENDER_BROWSER'])
        assert sha(full_sandbox)==full_before
        commands=[('observer_control',[sys.executable,'-I',str(script),'/usr/bin/true']),
            ('full_uninstrumented',[str(full_sandbox),'--version']),
            ('headless_uninstrumented',[str(headless),'--version']),
            ('headless_observed',[sys.executable,'-I',str(script),str(headless),'--version'])]
        for name,command in commands:
            process,kernel=run_isolated(command,workspace=stage,policy=policy,timeout_s=10,max_output_bytes=64*1024)
            assert kernel['kernel_enforced'] and kernel['resource_limits']==asdict(policy)
            assert kernel['no_new_privileges']
            observations.append(dict(name=name,command=command,process=asdict(process),kernel_policy=kernel))
        assert observations[0]['process']['process']['passed']
        assert 'DIAGNOSTIC_OBSERVER_LOADED_RLIMIT_AS=8589934592' in observations[0]['process']['process']['stderr']
        assert inventory(source)==headless_before and inventory(DEST)==headless_before
        assert sha(full)==full_before and sha(probe)==probe_before
        version_process=observations[2]['process']['process']
        compatible=version_process['passed'] and EXPECTED_VERSION in version_process['stdout']
        receipt=dict(schema='bie.section18.browser-compatibility-diagnostic/1',
            authority='EXPLICIT_HUMAN_BOUNDED_CHROMIUM_COMPATIBILITY_INVESTIGATION',
            playwright_version='1.57.0',registry_sha256=sha(metadata),registry_pins={k:pins[k] for k in ('chromium','chromium-headless-shell')},
            full_browser_sha256=full_before,headless_browser_sha256=sha(original),headless_files=headless_before,
            provisioning_command=copy,observer_build_command=build,observer_sha256=sha(observer),observations=observations,
            address_space_bytes=8589934592,security_controls_changed=False,dependencies_unchanged=True,
            production_browser_selection_changed=False,production_environment_changed=False,
            isolated_headless_version_probe_succeeded=compatible,distinct_test_methods=0,
            render_gate_authorized=False,actual_paint_gate_authorized=False,product_accepted=False)
        args.output.mkdir(parents=True)
        (args.output/'DIAGNOSTIC.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps(dict(diagnostic_only=True,isolated_headless_version_probe_succeeded=compatible,
            observations=[dict(name=r['name'],exit_code=r['process']['process']['exit_code'],
                stdout=r['process']['process']['stdout'],stderr=r['process']['process']['stderr']) for r in observations],
            security_controls_changed=False,render_gate_authorized=False)))
    return 0
if __name__=='__main__':raise SystemExit(main())
