"""Owned host-only resource diagnostic; NOT a production browser broker.

The unchanged canonical namespace launcher still sets BOTH Node AS limits to
8GiB. An external host supervisor adjusts only a verified stopped, immutable
diagnostic browser launcher, immediately before exec of the pinned Chromium.
No privilege or cgroup mount is exposed to the workload. Real cgroup memory
OOM controls run BEFORE a finite Chromium-only VAS experiment is admitted.
There is no user-controlled executable, URL, code, cgroup or PID input.
"""
from pathlib import Path
from dataclasses import asdict
import argparse,hashlib,json,os,resource,shutil,signal,subprocess,sys,tempfile,time

ROOT=Path(__file__).resolve().parents[1]
CGROOT=Path('/sys/fs/cgroup')
GIB=1024**3;MIB=1024**2;NODE_AS=8*GIB
BROWSER=Path('/usr/local/lib/bie-section18-chromium/chrome')
BROWSER_HASH='2e61bc3fd990bd4d7b419ef6b6303c67aaed683e5b83b3b25e416f015f343209'
SCRIPT_NAME='tools/diagnose_section18_chromium_resource_policy.py'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def values(path):return {k:int(v) for k,v in (line.split() for line in path.read_text().splitlines())}
def stopped(pid):
    try:return Path('/proc',str(pid),'status').read_text().split('State:',1)[1].lstrip().startswith('T')
    except (FileNotFoundError,IndexError):return False
def wait_stopped(child):
    end=time.monotonic()+5
    while time.monotonic()<end:
        if stopped(child.pid):return
        if child.poll() is not None:raise RuntimeError('CHILD_EXIT_BEFORE_ADMISSION')
        time.sleep(.01)
    raise RuntimeError('CHILD_ADMISSION_DEADLINE')

class Group:
    def __init__(self,limit):
        assert type(limit) is int and 64*MIB<=limit<=2*GIB
        assert CGROOT.resolve()==CGROOT and not CGROOT.is_symlink()
        assert any(' - cgroup2 ' in line and line.split()[4]==str(CGROOT)
                   for line in Path('/proc/self/mountinfo').read_text().splitlines())
        assert {'memory','pids'}<=set((CGROOT/'cgroup.subtree_control').read_text().split()), 'CGROUP_CONTROLLER_NOT_DELEGATED'
        # Do not enable global controllers or change an existing cgroup.
        self.path=Path(tempfile.mkdtemp(prefix='bie-s18-resource-probe-',dir=CGROOT))
        self.identity=self.path.stat().st_ino;self.limit=limit
        for name,value in [('memory.max',limit),('memory.swap.max',0),('memory.oom.group',1),('pids.max',128)]:
            (self.path/name).write_text(str(value))
            assert int((self.path/name).read_text())==value
        assert (self.path/'cgroup.kill').exists()
    def join(self,pid):
        assert pid!=os.getpid() and stopped(pid)
        (self.path/'cgroup.procs').write_text(str(pid))
        assert f'0::/{self.path.name}\n'==Path('/proc',str(pid),'cgroup').read_text()
    def members(self):return set(map(int,(self.path/'cgroup.procs').read_text().split()))
    def receipt(self):
        return dict(memory_max=int((self.path/'memory.max').read_text()),
                    swap_max=int((self.path/'memory.swap.max').read_text()),
                    oom_group=int((self.path/'memory.oom.group').read_text()),
                    pids_max=int((self.path/'pids.max').read_text()),
                    memory_peak=int((self.path/'memory.peak').read_text()),
                    memory_events=values(self.path/'memory.events'),events=values(self.path/'cgroup.events'),
                    host_supervisor_outside_workload=True)
    def close(self):
        assert self.path.parent==CGROOT and self.path.name.startswith('bie-s18-resource-probe-')
        assert not self.path.is_symlink() and self.path.stat().st_ino==self.identity
        assert os.getpid() not in self.members()
        (self.path/'cgroup.kill').write_text('1')
        end=time.monotonic()+5
        while values(self.path/'cgroup.events')['populated'] and time.monotonic()<end:time.sleep(.01)
        assert not values(self.path/'cgroup.events')['populated'], 'CGROUP_NOT_EMPTY_AFTER_KILL'
        self.path.rmdir() # exact freshly owned empty cgroup; no recursive removal

def child(mode,stage=None,output=None):
    resource.setrlimit(resource.RLIMIT_AS,(NODE_AS,NODE_AS))
    resource.setrlimit(resource.RLIMIT_CPU,(120,120))
    resource.setrlimit(resource.RLIMIT_FSIZE,(GIB,GIB))
    resource.setrlimit(resource.RLIMIT_NOFILE,(256,256))
    resource.setrlimit(resource.RLIMIT_NPROC,(128,128))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    os.kill(os.getpid(),signal.SIGSTOP)
    if mode in ('memory-positive','memory-negative'):
        size=8*MIB if mode=='memory-positive' else 128*MIB
        data=bytearray(size)
        for index in range(0,size,4096):data[index]=37
        print(json.dumps(dict(allocated_bytes=size,touched_pages=size//4096,as_limit=resource.getrlimit(resource.RLIMIT_AS))),flush=True)
        return 0
    assert mode=='namespace'
    sys.path.insert(0,str(ROOT))
    from bie.compiler.linux_worker import WorkerPolicy,run_isolated
    policy=WorkerPolicy();assert policy.address_space_bytes==NODE_AS
    node=Path('/opt/nvm/versions/node/v22.16.0/bin/node')
    result,kernel=run_isolated([str(node),str(Path(stage)/'probe.cjs')],workspace=stage,engine=ROOT,
        policy=policy,timeout_s=35,max_output_bytes=256*1024,lock_root=Path(stage)/'worker-slots')
    Path(output).write_text(json.dumps(dict(process=asdict(result),kernel_policy=kernel),indent=2)+'\n')
    assert kernel['kernel_enforced'] and kernel['resource_limits']==asdict(policy)
    return 0 if result.process.passed else 1

def browser_child():
    # Source is immutable in /engine; there is no arbitrary executable argument.
    assert len(sys.argv)==2 and sys.argv[1]=='browser'
    assert resource.getrlimit(resource.RLIMIT_AS)==(NODE_AS,NODE_AS)
    status=Path('/proc/self/status').read_text()
    assert '\nNoNewPrivs:\t1\n' in status
    assert all('\n'+key+':\t0000000000000000\n' in status for key in ('CapEff','CapPrm','CapInh','CapBnd'))
    assert '\nSeccomp:\t2\n' in status
    os.kill(os.getpid(),signal.SIGSTOP)
    limits=resource.getrlimit(resource.RLIMIT_AS)
    assert limits in ((512*GIB,512*GIB),(2*1024*GIB,2*1024*GIB))
    assert sha(BROWSER)==BROWSER_HASH
    argv=[str(BROWSER),'--headless','--no-sandbox','--disable-gpu','--remote-debugging-address=127.0.0.1',
          '--remote-debugging-port=9222','--user-data-dir=/tmp/bie-browser-probe','--no-first-run','about:blank']
    print(json.dumps(dict(browser_argv=argv,as_limit=limits,status_before_browser=status,
                         diagnostic_only=True)),flush=True)
    # --no-sandbox is inside the original BIE kernel sandbox, as with Remotion's
    # existing launcher. This does not claim a standalone host browser is secure.
    os.execve(str(BROWSER),argv,dict(os.environ))

def memory_control(negative):
    group=Group(64*MIB);child_process=None
    try:
        argv=[sys.executable,'-I',str(Path(__file__).resolve()),'child',
              'memory-negative' if negative else 'memory-positive']
        child_process=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        wait_stopped(child_process);group.join(child_process.pid);os.kill(child_process.pid,signal.SIGCONT)
        stdout,stderr=child_process.communicate(timeout=10)
        receipt=group.receipt()
        if negative:
            assert child_process.returncode==-signal.SIGKILL and receipt['memory_events']['oom_kill']>=1
            assert b'allocated_bytes' not in stdout
        else:
            assert child_process.returncode==0 and receipt['memory_events']['oom_kill']==0
            assert json.loads(stdout)['allocated_bytes']==8*MIB
        return dict(kind='OOM_NEGATIVE' if negative else 'POSITIVE',command=argv,
                    exit_code=child_process.returncode,kernel=receipt,stdout=stdout.decode(),stderr=stderr.decode(),passed=True)
    finally:
        group.close()
        if child_process is not None:
            if child_process.poll() is None:child_process.kill()
            child_process.communicate(timeout=2)

def proc_snapshot(pid):
    proc=Path('/proc',str(pid))
    try:
        executable=os.readlink(proc/'exe')
        if not executable.endswith('/chrome'):return None
        maps=(proc/'maps').read_text()
        spans=[]
        for line in maps.splitlines():
            address,perms,*rest=line.split()
            first,last=(int(x,16) for x in address.split('-'))
            if last-first>=GIB:spans.append(dict(bytes=last-first,permissions=perms))
        return dict(pid=pid,exe=executable,limits=list(resource.prlimit(pid,resource.RLIMIT_AS)),
                    status=(proc/'status').read_text(),large_mappings=spans,
                    maps_sha256=hashlib.sha256(maps.encode()).hexdigest())
    except (FileNotFoundError,ProcessLookupError,PermissionError):return None

def browser_probe(limit,output):
    assert limit in (512*GIB,2*1024*GIB)
    group=Group(2*GIB);outer=None;grant=None;snapshots={}
    try:
        with tempfile.TemporaryDirectory(prefix='bie-s18-browser-boundary-') as tmp:
            private=Path(tmp);stage=private/'project';stage.mkdir()
            # A host-root process mapped into a new user namespace does NOT
            # retain init-namespace DAC override for runner-owned private HOME.
            # Stage ONLY the required trusted code under this root-owned private
            # temp parent. Do not chmod/chown the runner's checkout or HOME.
            engine=private/'engine';(engine/'bie').mkdir(parents=True);(engine/'tools').mkdir()
            shutil.copyfile(ROOT/'bie/__init__.py',engine/'bie/__init__.py')
            source_compiler=ROOT/'bie/compiler'
            source_rows=[]
            for path in sorted(source_compiler.rglob('*')):
                assert not path.is_symlink(), 'TRUSTED_DIAGNOSTIC_SOURCE_LINK'
                if path.is_file() and path.suffix in ('.py','.js','.cjs','.json'):
                    assert len(source_rows)<1500 and path.stat().st_size<=8*MIB
                    source_rows.append((path.relative_to(ROOT).as_posix(),sha(path)))
            assert source_rows and sum((ROOT/name).stat().st_size for name,digest in source_rows)<=64*MIB
            for name,digest in source_rows:
                destination=engine/name;destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/name,destination);assert sha(destination)==digest
            for name in (SCRIPT_NAME,'tools/section18_chromium_resource_probe.cjs'):
                shutil.copyfile(ROOT/name,engine/name);assert sha(engine/name)==sha(ROOT/name)
            shutil.copyfile(ROOT/'tools/section18_chromium_resource_probe.cjs',stage/'probe.cjs')
            (stage/'worker-slots').mkdir()
            argv=[sys.executable,'-I','-B',str(engine/SCRIPT_NAME),'child','namespace',str(stage),str(output)]
            outer=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            wait_stopped(outer);group.join(outer.pid);os.kill(outer.pid,signal.SIGCONT)
            end=time.monotonic()+40
            while outer.poll() is None and time.monotonic()<end:
                members=group.members()
                assert len(members)<=128
                for pid in sorted(members):
                    proc=Path('/proc',str(pid))
                    try:command=(proc/'cmdline').read_bytes().split(b'\0')[:-1]
                    except FileNotFoundError:continue
                    expected=[b'/opt/pyvenv/bin/python',b'-I',b'/engine/'+SCRIPT_NAME.encode(),b'browser']
                    if grant is None and command==expected and stopped(pid):
                        # Forensic allowlist, not a public or workload-accessible
                        # arbitrary-PID resource API. Source/parent/cgroup verified.
                        assert sha(proc/'root/engine'/SCRIPT_NAME)==sha(Path(__file__).resolve())
                        assert sha(proc/'exe')==sha(Path('/opt/pyvenv/bin/python').resolve())
                        parent=int((proc/'status').read_text().split('PPid:',1)[1].split()[0])
                        assert parent in group.members()
                        assert os.readlink(Path('/proc',str(parent),'exe')).endswith('/node')
                        node_before=resource.prlimit(parent,resource.RLIMIT_AS)
                        assert node_before==(NODE_AS,NODE_AS)
                        original=resource.prlimit(pid,resource.RLIMIT_AS,(limit,limit))
                        assert original==(NODE_AS,NODE_AS)
                        assert resource.prlimit(parent,resource.RLIMIT_AS)==node_before
                        grant=dict(host_pid=pid,parent_node_pid=parent,old_limit=list(original),new_limit=[limit,limit],
                                   node_limit_before=list(node_before),node_limit_after=list(resource.prlimit(parent,resource.RLIMIT_AS)),
                                   only_verified_browser_launcher_modified=True,exact_argv=[x.decode() for x in command])
                        os.kill(pid,signal.SIGCONT)
                    snap=proc_snapshot(pid)
                    if snap:
                        old=snapshots.get(pid)
                        if old is None or sum(m['bytes'] for m in snap['large_mappings'])>sum(m['bytes'] for m in old['large_mappings']):snapshots[pid]=snap
                time.sleep(.02)
            if outer.poll() is None:raise RuntimeError('PROBE_HOST_DEADLINE')
            stdout,stderr=outer.communicate(timeout=2)
            receipt=group.receipt()
            # Retain the FIRST inner failure before enforcing the admission
            # assertion. A missing browser grant must not hide namespace/Node
            # failure behind a secondary diagnostic-supervisor error.
            host_result=dict(outer_exit_code=outer.returncode,stdout=stdout.decode(),stderr=stderr.decode(),
                             grant=grant,kernel_cgroup=receipt,snapshots=list(snapshots.values()),
                             browser_limit=limit,diagnostic_only=True,
                             trusted_source_rows=[dict(path=name,sha256=digest) for name,digest in source_rows],
                             source_bytes_unchanged=all(sha(engine/name)==digest for name,digest in source_rows),
                             original_checkout_or_HOME_permissions_changed=False)
            assert host_result['source_bytes_unchanged']
            output.with_name(output.stem+'_HOST.json').write_text(json.dumps(host_result,indent=2)+'\n')
            assert grant is not None,'NO_VERIFIED_BROWSER_ADMISSION'
            assert outer.returncode==0,(stdout.decode(),stderr.decode(),output.read_text() if output.exists() else '')
            original=json.loads(output.read_text());kernel=original['kernel_policy']
            assert kernel['kernel_enforced'] and kernel['resource_limits']['address_space_bytes']==NODE_AS
            assert kernel['capabilities_dropped'] and kernel['no_new_privileges']
            assert kernel['private_network']=='LOOPBACK_ONLY_NO_HOST_ROUTE'
            node=json.loads(original['process']['process']['stdout'])
            assert node['node']=='v22.16.0' and node['execArgv']==[]
            assert node['limits_before']==node['limits_after']
            assert json.loads(node['actual_browser_javascript_result'])['arithmetic']==42
            assert all(s['limits']==[limit,limit] for s in snapshots.values())
            assert receipt['memory_events']['oom_kill']==0
            browser_start=json.loads(node['browser_startup'])
            assert browser_start['as_limit']==[limit,limit]
            return dict(command=argv,browser_limit=limit,grant=grant,kernel_cgroup=receipt,
                        canonical_worker_receipt=original,browser_process_snapshots=list(snapshots.values()),
                        startup_scope_receipt=browser_start,diagnostic_passed=True,
                        full_V8_sandbox_attestation_not_inferred_from_launch=True,
                        native_render_gate_passed=False)
    finally:
        group.close()
        if outer is not None:
            if outer.poll() is None:outer.kill()
            outer.communicate(timeout=2)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    assert sys.platform=='linux' and os.getuid()==0 and not args.output.exists()
    assert sha(BROWSER)==BROWSER_HASH
    assert subprocess.check_output(['/opt/nvm/versions/node/v22.16.0/bin/node','--version'],text=True).strip()=='v22.16.0'
    args.output.mkdir(parents=True)
    result=dict(schema='bie.section18.chromium-resource-diagnostic/1',diagnostic_only=True,
                production_sources_changed=False,render_gate_passed=False,product_accepted=False,
                original_worker_node_address_space_bytes=NODE_AS,browser_sha256=sha(BROWSER),
                cgroup_root_controller_configuration_changed=False,controls=[],browser_probes=[])
    receipt=args.output/'DIAGNOSTIC.json'
    try:
        for negative in (False,True):
            result['controls'].append(memory_control(negative));receipt.write_text(json.dumps(result,indent=2)+'\n')
        for limit in (512*GIB,2*1024*GIB):
            try:
                probe=browser_probe(limit,args.output/f'WORKER_{limit}.json')
            except (AssertionError,RuntimeError) as error:
                # A lower reservation experiment may fail. Preserve it and
                # still execute the separately bounded larger experiment; never
                # turn this diagnostic failure into a native renderer PASS.
                probe=dict(browser_limit=limit,diagnostic_passed=False,
                           failure_type=type(error).__name__,failure=str(error)[:6000])
            result['browser_probes'].append(probe)
            receipt.write_text(json.dumps(result,indent=2)+'\n')
        result['diagnostic_completed']=all(p['diagnostic_passed'] for p in result['browser_probes'])
        assert result['browser_probes'][-1]['diagnostic_passed'], 'BOUNDED_2TIB_BROWSER_EXPERIMENT_FAILED'
    except BaseException as error:
        result.update(diagnostic_completed=False,failure_type=type(error).__name__,failure=str(error)[:6000])
        raise
    finally:
        result['browser_bytes_unchanged']=sha(BROWSER)==BROWSER_HASH
        receipt.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(dict(diagnostic_completed=result['diagnostic_completed'],
            physical_memory_controls=len(result['controls']),browser_probes=len(result['browser_probes']),
            render_gate_passed=False)))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='browser':browser_child()
    elif len(sys.argv)>2 and sys.argv[1]=='child':
        raise SystemExit(child(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else None,sys.argv[4] if len(sys.argv)>4 else None))
    else:main()
