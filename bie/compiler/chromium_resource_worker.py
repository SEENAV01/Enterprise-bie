"""H1-008: host-owned Chromium-only compatibility boundary.

Not a generic privilege/PID API. Only governed H3 paint/Remotion commands may
use it, from an explicitly provisioned root supervisor. The existing kernel
worker stays unchanged and gives Node exactly8GiB. A stopped immutable browser
entry, with a verified pinned Node parent, receives finite2TiB VAS. ALL workload
descendants remain in a private2GiB-memory/swap0/pids128 cgroup. No fallback.
"""
from pathlib import Path
from dataclasses import asdict
import contextlib,hashlib,json,math,os,re,shutil,subprocess,sys,tempfile,time
if __package__ in (None, ''):
    # Private, host-owned driver only; -I excludes user startup/PYTHONPATH.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from bie.compiler.qa_common import CompilerQAError
else:
    from .qa_common import CompilerQAError

NODE_AS=8*1024**3
CHROME_AS=2*1024**4
PHYSICAL_MEMORY=2*1024**3
CHROME_SHA='2e61bc3fd990bd4d7b419ef6b6303c67aaed683e5b83b3b25e416f015f343209'
ENTRY='/engine/bie/compiler/qa_support/chromium_resource_entry.py'
POLICY='bie/compiler/qa_support/chromium-boundary.json'
CGROOT=Path('/sys/fs/cgroup')
FIXED_ARGS=frozenset(('about:blank --allow-pre-commit-input --disable-background-networking '
 '--enable-features=NetworkService,NetworkServiceInProcess,CanvasDrawElement '
 '--disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-breakpad '
 '--disable-client-side-phishing-detection --disable-component-extensions-with-background-pages '
 '--disable-default-apps --disable-dev-shm-usage --no-proxy-server --proxy-bypass-list=* '
 '--force-gpu-mem-available-mb=4096 --disable-hang-monitor --disable-extensions --allow-chrome-scheme-url '
 '--disable-ipc-flooding-protection --disable-popup-blocking --disable-prompt-on-repost '
 '--disable-renderer-backgrounding --disable-sync --force-color-profile=srgb --metrics-recording-only '
 '--mute-audio --no-first-run --enable-automation --password-store=basic --use-mock-keychain '
 '--enable-blink-features=IdleDetection --export-tagged-pdf --intensive-wake-up-throttling-policy=0 '
 '--no-sandbox --disable-setuid-sandbox --use-gl=angle --use-angle=swiftshader '
 '--disable-background-media-suspend --allow-running-insecure-content --disable-component-update '
 '--disable-domain-reliability --disable-print-preview --disable-site-isolation-trials '
 '--disk-cache-size=268435456 --hide-scrollbars --no-default-browser-check --no-pings '
 '--font-render-hinting=none --no-zygote --ignore-gpu-blocklist --enable-unsafe-webgpu '
 '--remote-debugging-port=0').split()) | frozenset(("--proxy-server='direct://'",
 '--disable-features=AudioServiceOutOfProcess,IsolateOrigins,site-per-process,Translate,BackForwardCache,AvoidUnnecessaryBeforeUnloadCheckSync,IntensiveWakeUpThrottling,LocalNetworkAccessChecks,BlockInsecurePrivateNetworkRequests,PrivateNetworkAccessSendPreflights,PrivateNetworkAccessRespectPreflightResults'))

def require(condition,code):
    if not condition:raise CompilerQAError('CHROMIUM_RESOURCE_'+code)

def validate_browser_args(args):
    """Exact pinned Remotion defaults plus bounded generated numeric/temp values.

    No new V8/allocator flags, arbitrary URL, extension, preload, executable,
    single-process, web-security/certificate bypass or remote debug address.
    Existing Remotion defaults are preserved, not added by this adapter.
    """
    require(type(args) in (list,tuple) and 4<=len(args)<=80,'ARGS')
    require(all(type(a) is str and 0<len(a)<=1024 and not any(ord(c)<32 for c in a) for a in args),'ARGS')
    require(len(args)==len(set(args)),'DUPLICATE_ARG')
    for arg in args:
        if arg in FIXED_ARGS or arg in ('--headless=old','--headless=new'):continue
        if re.fullmatch(r'--video-threads=([1-9]|[1-9][0-9]|1[01][0-9]|12[0-8])',arg):continue
        if re.fullmatch(r'--user-data-dir=/tmp/puppeteer_dev_chrome_profile-[A-Za-z0-9_-]{1,64}',arg):continue
        if re.fullmatch(r'--force-device-scale-factor=(1|2|3|4)(\.0)?',arg):continue
        if re.fullmatch(r'--window-size=[1-9][0-9]{1,3},[1-9][0-9]{1,3}',arg):continue
        raise CompilerQAError('CHROMIUM_RESOURCE_ARG_NOT_PINNED')
    require(all(a in args for a in ('about:blank','--no-sandbox','--remote-debugging-port=0')),'REQUIRED_ARG')
    require(sum(a.startswith('--headless=') for a in args)==1 and '--headless=new' in args,'HEADLESS_ARG')
    require(sum(a.startswith('--user-data-dir=') for a in args)==1,'PROFILE_ARG')
    return tuple(args)

def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1024**2),b''):h.update(part)
    return h.hexdigest()

def bounded_read(path,maximum=65536):
    with Path(path).open('rb') as f:data=f.read(maximum+1)
    require(len(data)<=maximum,'CONTROL_SIZE');return data

def proc_status(pid):
    return dict(line.split(':',1) for line in bounded_read(Path('/proc',str(pid),'status')).decode().splitlines())

def stopped(pid):
    try:return proc_status(pid)['State'].lstrip().startswith('T')
    except (FileNotFoundError,ProcessLookupError):return False

def counters(path):return dict((k,int(v)) for k,v in (row.split() for row in bounded_read(path).decode().splitlines()))

def owned_browser_executable(executable,child_root,browser,owned_root):
    """Host proc links may include the exact admitted child's private root."""
    return child_root==owned_root and executable in (str(browser),owned_root+str(browser))

def validate_entry_mappings(mappings, mountinfo, host_root=None):
    """Admit executable libraries ONLY on the existing canonical read-only mounts.

    Namespace bind-mounts retain /lib and /lib64 target names, even on merged-/usr
    hosts. Prefix alone is not enough: inspect the deepest actual mount's ro bit.
    Anonymous, deleted, workspace/engine or writable executable mappings fail.
    """
    fixed=('/usr','/lib','/lib64','/bin','/sbin','/opt/pyvenv')
    mounts=[]
    for row in mountinfo.splitlines():
        fields=row.split();require(len(fields)>=10 and '-' in fields,'MOUNTINFO')
        mounts.append((fields[4],set(fields[5].split(','))))
    checked=[]
    for row in mappings.splitlines():
        fields=row.split();require(len(fields)>=5,'EXECUTABLE_MAPPING')
        permissions=fields[1]
        if 'x' not in permissions:continue
        require('w' not in permissions and len(fields)==6,'EXECUTABLE_MAPPING')
        name=fields[5]
        if name in ('[vdso]','[vsyscall]'):continue
        if host_root is not None and name.startswith(host_root+'/'):
            # Host proc maps use the exact sandbox-root prefix; mountinfo is
            # already relative to the frozen child's chroot. No fuzzy alias.
            name=name[len(host_root):]
        require(any(name.startswith(prefix+'/') for prefix in fixed),'EXECUTABLE_MAPPING')
        candidates=[(path,flags) for path,flags in mounts if name==path or name.startswith(path.rstrip('/')+'/')]
        require(bool(candidates),'EXECUTABLE_MAPPING_MOUNT')
        path,flags=max(candidates,key=lambda r:len(r[0]))
        require(path in fixed and 'ro' in flags and 'rw' not in flags,'EXECUTABLE_MAPPING_WRITABLE')
        checked.append(dict(path=name,read_only_mount=path))
    require(bool(checked),'EXECUTABLE_MAPPING_EMPTY');return checked

class OwnedMemoryGroup:
    def __init__(self):
        require(sys.platform=='linux' and os.getuid()==0,'HOST_SUPERVISOR_REQUIRED')
        require(CGROOT.resolve()==CGROOT and not CGROOT.is_symlink(),'CGROUP_PATH')
        require(any(' - cgroup2 ' in row and row.split()[4]==str(CGROOT)
            for row in bounded_read('/proc/self/mountinfo',1024**2).decode().splitlines()),'CGROUP2_REQUIRED')
        require({'memory','pids'}<=set(bounded_read(CGROOT/'cgroup.subtree_control').decode().split()),'CGROUP_NOT_DELEGATED')
        self.path=Path(tempfile.mkdtemp(prefix='bie-chromium-owned-',dir=CGROOT));self.inode=self.path.stat().st_ino
        try:
            for name,value in [('memory.max',PHYSICAL_MEMORY),('memory.swap.max',0),('memory.oom.group',1),('pids.max',128)]:
                (self.path/name).write_text(str(value));require(int((self.path/name).read_text())==value,'CGROUP_LIMIT')
            require((self.path/'cgroup.kill').exists() and (self.path/'cgroup.freeze').exists(),'CGROUP_CONTROLS')
        except BaseException:
            # No workload has been admitted. Delete only our verified empty leaf.
            require(self.path.parent==CGROOT and not self.path.is_symlink() and
                self.path.stat().st_ino==self.inode and not self.members(),'CGROUP_SETUP_CLEANUP')
            self.path.rmdir()
            raise
    def members(self):return set(map(int,bounded_read(self.path/'cgroup.procs').split()))
    def join(self,pid):
        require(pid!=os.getpid() and stopped(pid),'ADMISSION_STOP')
        (self.path/'cgroup.procs').write_text(str(pid));self.verify_member(pid)
    def verify_member(self,pid):
        require(bounded_read(Path('/proc',str(pid),'cgroup'))==f'0::/{self.path.name}\n'.encode(),'FOREIGN_PROCESS')
    def freeze(self,value):
        (self.path/'cgroup.freeze').write_text(str(int(value)));end=time.monotonic()+2
        while counters(self.path/'cgroup.events')['frozen']!=int(value):
            require(time.monotonic()<end,'FREEZE_DEADLINE');time.sleep(.005)
    def receipt(self):
        return dict(memory_max=int((self.path/'memory.max').read_text()),swap_max=int((self.path/'memory.swap.max').read_text()),
            pids_max=int((self.path/'pids.max').read_text()),memory_peak=int((self.path/'memory.peak').read_text()),
            memory_events=counters(self.path/'memory.events'),events=counters(self.path/'cgroup.events'),
            controller_configuration_changed=False,host_supervisor_inside_workload=False)
    def close(self):
        require(self.path.parent==CGROOT and self.path.name.startswith('bie-chromium-owned-') and
            not self.path.is_symlink() and self.path.stat().st_ino==self.inode and os.getpid() not in self.members(),'CLEANUP_IDENTITY')
        (self.path/'cgroup.kill').write_text('1');self.freeze(False);end=time.monotonic()+5
        while counters(self.path/'cgroup.events')['populated']:
            require(time.monotonic()<end,'CLEANUP_DEADLINE');time.sleep(.01)
        self.path.rmdir() # only this verified, freshly owned empty cgroup

def _trusted_engine(source,destination):
    rows=[];total=0
    require(source.resolve()==source and source==Path(__file__).resolve().parents[2] and
            source.stat().st_uid==0 and not source.stat().st_mode&0o022,'TRUSTED_ENGINE_REQUIRED')
    (destination/'bie').mkdir(parents=True)
    for p in [source/'bie/__init__.py', *sorted((source/'bie/compiler').rglob('*'))]:
        require(not p.is_symlink(),'ENGINE_LINK')
        if p.is_file() and p.suffix in ('.py','.js','.cjs','.json'):
            require(p.stat().st_uid==0 and not p.stat().st_mode&0o022,'ENGINE_OWNER')
            require(len(rows)<1500 and p.stat().st_size<8*1024**2,'ENGINE_SIZE')
            name=p.relative_to(source);q=destination/name;q.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,q);digest=file_sha(p);require(file_sha(q)==digest,'ENGINE_CHANGED')
            total+=q.stat().st_size;require(total<64*1024**2,'ENGINE_SIZE')
            rows.append(dict(path=name.as_posix(),sha256=digest))
    require(bool(rows),'ENGINE_EMPTY');return rows

def _driver(config):
    """Host-only private config; it is never mounted into the workload."""
    import resource,signal
    from .linux_worker import run_isolated,WorkerPolicy
    from .artifact_hashing import canonical_json
    # Unshare's host-side temporary directories are owned by the supervisor too.
    # A killed driver must not strand them outside its parent's recovery scope.
    tempfile.tempdir=config['private_temporary']
    resource.setrlimit(resource.RLIMIT_AS,(NODE_AS,NODE_AS));os.kill(os.getpid(),signal.SIGSTOP)
    try:
        process,kernel=run_isolated(config['command'],workspace=config['workspace'],engine=config['engine'],
            writable=config['writable'],policy=WorkerPolicy(**config['policy']),timeout_s=config['timeout_s'],
            max_output_bytes=config['max_output_bytes'],secrets=config['secrets'],lock_root=config['lock_root'])
        Path(config['result']).write_bytes(canonical_json(dict(process=asdict(process),kernel=kernel)))
    except BaseException as error:
        Path(config['result']).write_bytes(canonical_json(dict(driver_failure=type(error).__name__,
            diagnostic=str(error)[:16384])))
        return 2
    return 0

def _grant(group,pid,expected_parent_command,entry_hash,node_hash,source_policy_hash,owned_control_root=None):
    """Freeze this whole owned workload, preventing parent reap/PID reuse.

    Parent Node is a governed immutable H3 producer. No arbitrary command or
    caller-supplied PID/grant is exposed. Recheck PID identity/parent/namespace/
    source/environment/cgroup under freeze before and after exact prlimit.
    """
    import resource,signal
    group.freeze(True)
    try:
        group.verify_member(pid);require(stopped(pid),'ENTRY_NOT_STOPPED')
        status=proc_status(pid);parent=int(status['PPid']);group.verify_member(parent)
        proc=Path('/proc',str(pid));pp=Path('/proc',str(parent));start=bounded_read(proc/'stat').split()[21]
        require(bounded_read(pp/'cmdline').split(b'\0')[:-1]==[s.encode() for s in expected_parent_command],'PARENT_COMMAND')
        require(file_sha(pp/'exe')==node_hash and file_sha(proc/'exe')==file_sha(Path('/opt/pyvenv/bin/python').resolve()),'EXECUTABLE_IDENTITY')
        require(file_sha(proc/'root'/ENTRY.lstrip('/'))==entry_hash,'ENTRY_CHANGED')
        require(file_sha(proc/'root/engine'/POLICY)==source_policy_hash,'POLICY_CHANGED')
        require(status['NoNewPrivs'].strip()=='1' and status['Seccomp'].strip()=='2' and
            all(status[name].strip()=='0000000000000000' for name in ('CapEff','CapPrm','CapInh','CapBnd')),'ENTRY_SECURITY')
        environment=bounded_read(proc/'environ').split(b'\0')
        require(not any(row.startswith((b'LD_',b'NODE_OPTIONS=',b'PYTHONHOME=',b'PYTHONSTARTUP=')) for row in environment),'ENTRY_ENVIRONMENT')
        map_text=bounded_read(proc/'maps',2*1024**2).decode()
        mount_text=bounded_read(proc/'mountinfo',1024**2).decode()
        sandbox_root=os.readlink(proc/'root')
        require(owned_control_root is not None and Path(sandbox_root).name=='root' and
                Path(sandbox_root).parent.parent==Path(owned_control_root) and
                Path(sandbox_root).parent.name.startswith('bie-worker-control-') and
                sandbox_root==os.readlink(pp/'root'),'OWNED_SANDBOX_ROOT')
        try:
            mappings=validate_entry_mappings(map_text,mount_text,sandbox_root)
        except CompilerQAError as error:
            # Retain the exact owned-entry mapping cause before any grant.
            # Metadata only: no environment, source content or secrets.
            error.mapping_diagnostic=dict(executable_rows=[r for r in map_text.splitlines() if 'x' in r.split()[1]],
                mountinfo=mount_text,maps_sha256=hashlib.sha256(map_text.encode()).hexdigest(),
                browser_grant_made=False)
            raise
        node_before=resource.prlimit(parent,resource.RLIMIT_AS)
        require(node_before==(NODE_AS,NODE_AS),'PARENT_LIMIT')
        require(resource.prlimit(pid,resource.RLIMIT_AS)==(NODE_AS,NODE_AS),'ENTRY_LIMIT')
        for name in ('user','net','mnt','pid'):
            require(os.readlink(proc/'ns'/name)==os.readlink(pp/'ns'/name) and
                    os.readlink(proc/'ns'/name)!=os.readlink(Path('/proc/self/ns')/name),'ENTRY_NAMESPACE')
        fd=os.pidfd_open(pid)
        try:
            original=resource.prlimit(pid,resource.RLIMIT_AS,(CHROME_AS,CHROME_AS))
            require(original==(NODE_AS,NODE_AS) and resource.prlimit(parent,resource.RLIMIT_AS)==node_before,'GRANT_SCOPE')
            group.verify_member(pid);require(bounded_read(proc/'stat').split()[21]==start,'PID_IDENTITY')
            signal.pidfd_send_signal(fd,signal.SIGCONT)
        finally:os.close(fd)
        return dict(pid=pid,parent_node_pid=parent,node_limit_before=list(node_before),
            node_limit_after=list(resource.prlimit(parent,resource.RLIMIT_AS)),chrome_limit=[CHROME_AS]*2,
            only_verified_browser_entry_modified=True,workload_frozen_during_grant=True,pidfd_used=True,
            entry_sha256=entry_hash,immutable_policy_sha256=source_policy_hash,
            readonly_executable_mappings=mappings,owned_sandbox_root=sandbox_root)
    finally:group.freeze(False)

def approved_command(command, root, browser, kind):
    """Pure admission: reject unrelated commands before any resource allocation."""
    require(type(command) in (list,tuple) and bool(command) and
        all(type(x) is str and x and '\0' not in x for x in command),'COMMAND')
    command=list(command)
    require(kind in ('actual-paint','renderer'),'COMMAND_KIND')
    node=command[0]
    require(node=='/opt/nvm/versions/node/v22.16.0/bin/node','NODE_PIN')
    if kind=='actual-paint':
        require(command==[node,'--disable-wasm-trap-handler',
            '/engine/bie/compiler/qa_support/remotion_raster_capture.cjs','/work/capture-request.json'],'PAINT_COMMAND')
    else:
        require(len(command)>=5 and command[1]==str(root/'node_modules/@remotion/cli/remotion-cli.js') and
            command[2]=='render','RENDER_COMMAND')
        browser_args=[a for a in command if a.startswith('--browser-executable=')]
        require(browser_args==['--browser-executable='+str(browser)],'RENDER_BROWSER')
        require(not any(a.startswith(('--disable-wasm','--js-flags','--node-options')) for a in command),'RENDER_NODE_FLAGS')
        require(not any(a.startswith('--chrome-mode') for a in command),'RENDER_CHROME_MODE')
        command.insert(1,'--disable-wasm-trap-handler')
        command=[('--browser-executable='+ENTRY) if a.startswith('--browser-executable=') else a for a in command]
        command.append('--chrome-mode=chrome-for-testing')
    return command

def run_chromium_isolated(command,*,workspace,engine,browser,kind,writable=(),policy=None,timeout_s=120,
                          cancel_event=None,max_output_bytes=2*1024**2,secrets=(),receipt_path=None):
    import resource,signal
    from .linux_worker import WorkerPolicy
    from .build_common import ProcessReceipt
    from .render_process import RenderProcessResult
    from .artifact_hashing import canonical_json
    require(sys.platform=='linux' and os.getuid()==0,'HOST_SUPERVISOR_REQUIRED')
    p=policy or WorkerPolicy();require(asdict(p)==asdict(WorkerPolicy()),'BASE_POLICY')
    require(type(timeout_s) in (int,float) and math.isfinite(timeout_s) and 0<timeout_s<=3600,'TIMEOUT_BOUND')
    require(type(max_output_bytes) is int and 0<max_output_bytes<=8*1024**2,'OUTPUT_BOUND')
    root=Path(workspace).absolute();source=Path(engine).absolute()
    command=approved_command(command,root,browser,kind);node=Path(command[0])
    require(node.is_file() and not node.is_symlink() and node.name=='node' and
            str(node).startswith('/opt/nvm/versions/node/v22.16.0/bin/'),'NODE_PIN')
    require(root.is_dir() and root.stat().st_uid==0 and not root.is_symlink(),'OWNED_WORKSPACE_REQUIRED')
    require(not root.stat().st_mode&0o022,'WORKSPACE_PERMISSIONS')
    browser=Path(browser);require(browser.is_file() and not browser.is_symlink() and
        str(browser).startswith('/usr/') and file_sha(browser)==CHROME_SHA,'BROWSER_PIN')
    if receipt_path is not None:
        dest=Path(receipt_path)
        require(dest.parent.is_dir() and not dest.exists() and not dest.is_symlink(),'RECEIPT_PATH')
    group=OwnedMemoryGroup();outer=None;grants=[];observed={};result=None;failure=None;temporary=None
    receipt=dict(schema='bie.chromium-resource-boundary/1',node_address_space_bytes=NODE_AS,
        chromium_address_space_bytes=CHROME_AS,physical_memory_bytes=PHYSICAL_MEMORY,swap_max=0,
        command=command,kind=kind,grants=grants,security_policy_weakened=False,accepted=False)
    try:
        temporary=tempfile.TemporaryDirectory(prefix='bie-chromium-private-')
        with contextlib.nullcontext(temporary.name) as tmp:
            private=Path(tmp);overlay=private/'engine';rows=_trusted_engine(source,overlay)
            entry=overlay/ENTRY.removeprefix('/engine/');entry.chmod(0o500)
            inner_policy=dict(schema='bie.chromium-entry-policy/1',browser=str(browser),browser_sha256=CHROME_SHA,
                              node_address_space_bytes=NODE_AS,chromium_address_space_bytes=CHROME_AS)
            (overlay/POLICY).write_bytes(canonical_json(inner_policy))
            source_policy_hash=file_sha(overlay/POLICY);entry_hash=file_sha(entry);node_hash=file_sha(node)
            output=private/'result.json';conf=private/'host-config.json'
            private_temporary=private/'worker-temporary';private_temporary.mkdir(mode=0o700)
            data=dict(command=command,workspace=str(root),engine=str(overlay),writable=list(writable),policy=asdict(p),
                timeout_s=timeout_s,max_output_bytes=max_output_bytes,secrets=list(secrets),
                lock_root='/tmp/bie-comp-worker-slots',result=str(output),private_temporary=str(private_temporary))
            conf.write_bytes(canonical_json(data));conf.chmod(0o600)
            driver=overlay/'bie/compiler/chromium_resource_worker.py'
            outer=subprocess.Popen([sys.executable,'-I','-B',str(driver),'--driver',str(conf)],
                stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,start_new_session=True)
            deadline=time.monotonic()+5
            while not stopped(outer.pid):
                require(outer.poll() is None and time.monotonic()<deadline,'DRIVER_ADMISSION');time.sleep(.01)
            group.join(outer.pid);os.kill(outer.pid,signal.SIGCONT)
            expected=[s.replace(str(root)+'/','/work/').replace(str(overlay)+'/','/engine/') for s in command]
            end=time.monotonic()+timeout_s+10
            while outer.poll() is None:
                if cancel_event is not None and cancel_event.is_set():failure='CANCELLED';break
                require(time.monotonic()<end,'HOST_DEADLINE');members=group.members();require(len(members)<=128,'PROCESS_BOUND')
                for pid in sorted(members):
                    proc=Path('/proc',str(pid))
                    try:argv=bounded_read(proc/'cmdline').split(b'\0')[:-1]
                    except (FileNotFoundError,ProcessLookupError):continue
                    prefix=[b'/opt/pyvenv/bin/python',b'-I',ENTRY.encode()]
                    if argv[:3]==prefix and stopped(pid):
                        require(len(grants)<4 and pid not in {g['pid'] for g in grants},'GRANT_BOUND')
                        validate_browser_args([x.decode() for x in argv[3:]])
                        granted=_grant(group,pid,expected,entry_hash,node_hash,source_policy_hash,private_temporary)
                        granted['browser_argv']=[x.decode() for x in argv[3:]]
                        grants.append(granted)
                    try:
                        granted=next((g for g in grants if g['pid']==pid),None)
                        if granted and owned_browser_executable(os.readlink(proc/'exe'),os.readlink(proc/'root'),
                                                               browser,granted['owned_sandbox_root']):
                            require(resource.prlimit(pid,resource.RLIMIT_AS)==(CHROME_AS,CHROME_AS),'CHROME_LIMIT')
                            maps=bounded_read(proc/'maps',2*1024**2).decode();spans=[]
                            for row in maps.splitlines():
                                first,last=(int(x,16) for x in row.split()[0].split('-'))
                                if last-first>=1024**3:spans.append(dict(bytes=last-first,permissions=row.split()[1]))
                            old=observed.get(pid,[])
                            if sum(r['bytes'] for r in spans)>sum(r['bytes'] for r in old):observed[pid]=spans
                    except (FileNotFoundError,ProcessLookupError):pass
                time.sleep(.01)
            if failure is None:
                _,stderr=outer.communicate(timeout=2)
                receipt['driver_stderr']=stderr.decode('utf-8',errors='replace')[:16384]
                require(len(stderr)<=65536 and output.exists(),'DRIVER_RESULT')
                v=json.loads(bounded_read(output,max_output_bytes*8+1024**2))
                if 'driver_failure' in v:
                    receipt['driver_failure']=v
                    raise CompilerQAError('CHROMIUM_RESOURCE_DRIVER_FAILED')
                require(outer.returncode==0,'DRIVER_EXIT')
                kernel=v['kernel'];require(kernel.get('kernel_enforced') is True and kernel.get('resource_limits')==asdict(p),'KERNEL_POLICY')
                value=v['process'];value['process']['command']=tuple(value['process']['command'])
                value['process']=ProcessReceipt(**value['process']);result=RenderProcessResult(**value)
                if result.process.passed:
                    require(bool(grants),'NO_BROWSER_ADMISSION')
                    require(any(row['bytes']>1024**4 for rows in observed.values() for row in rows),'FULL_RESERVATION_NOT_OBSERVED')
                receipt['kernel']=dict(kernel) # no recursive receipt reference
            receipt['trusted_engine_rows']=rows
            require(all(file_sha(overlay/r['path'])==r['sha256'] for r in rows),'ENGINE_CHANGED_AFTER_RUN')
            receipt['browser_bytes_unchanged']=file_sha(browser)==CHROME_SHA
    except BaseException as error:
        failure=failure or (str(error) if isinstance(error,CompilerQAError) else type(error).__name__)
        if hasattr(error,'mapping_diagnostic'):receipt['entry_mapping_diagnostic']=error.mapping_diagnostic
    finally:
        receipt['memory_cgroup']=group.receipt();receipt['browser_mappings']=observed
        if receipt['memory_cgroup']['memory_events']['oom_kill']:
            failure=failure or 'MEMORY_EXHAUSTED'
        try:
            group.close()
            receipt['owned_cgroup_removed']=True
        except BaseException as error:
            receipt['cleanup_failure']=str(error)[:1024]
            failure=failure or 'CLEANUP_FAILED'
        if outer is not None:
            if outer.poll() is None:outer.kill()
            outer.communicate(timeout=2)
        if temporary is not None and receipt.get('owned_cgroup_removed'):
            temporary.cleanup()
        receipt['owned_processes_reaped']=bool(receipt.get('owned_cgroup_removed') and (outer is None or outer.poll() is not None))
        receipt['failure']=failure
        receipt['process_passed']=bool(result and result.process.passed and failure is None)
        if receipt_path is not None:
            with Path(receipt_path).open('xb') as stream:stream.write(canonical_json(receipt))
    require(failure is None,'FAILED:'+str(failure));require(result is not None,'MISSING_RESULT')
    require(receipt['memory_cgroup']['memory_events']['oom_kill']==0,'MEMORY_EXHAUSTED')
    kernel['chromium_resource_boundary']=receipt
    return result,kernel

if __name__=='__main__':
    # Internal trusted host driver. Never executed from /engine by the workload.
    require(len(sys.argv)==3 and sys.argv[1]=='--driver' and os.getuid()==0,'DRIVER_ARGUMENTS')
    conf=Path(sys.argv[2]);require(conf.is_file() and not conf.is_symlink() and
        conf.stat().st_uid==0 and conf.stat().st_mode&0o077==0,'DRIVER_CONFIG')
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    from bie.compiler.chromium_resource_worker import _driver
    raise SystemExit(_driver(json.loads(bounded_read(conf,1024**2))))
