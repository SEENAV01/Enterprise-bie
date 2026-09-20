"""H7 operational worker. Execute only through the private namespace launcher.

Private host-owned control files are NOT mounted inside the workload. Filesystem
allowlists, a new network/PID namespace, dropped capabilities and a syscall filter
are enforced by the kernel. This is a Linux adapter, not a universal exploit proof.
"""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
from dataclasses import asdict, dataclass
import fcntl, json, os, shutil, sys, tempfile, time
from .qa_common import CompilerQAError
from .render_process import run_bounded_process
from .artifact_hashing import canonical_json
from .host_toolchain import file_identity

@dataclass(frozen=True)
class WorkerPolicy:
    procfs: bool = True
    concurrent_jobs: int = 2
    cpu_seconds: int = 120
    address_space_bytes: int = 8*1024**3
    file_bytes: int = 1024**3
    descriptors: int = 256
    processes: int = 128
    tmpfs_bytes: int = 512*1024**2
    def __post_init__(self):
        if type(self.procfs) is not bool:raise CompilerQAError('WORKER_POLICY_INVALID: procfs')
        limits={'concurrent_jobs':(1,8),'cpu_seconds':(1,3600),'address_space_bytes':(128*1024**2,512*1024**3),
                'file_bytes':(1024,8*1024**3),'descriptors':(32,4096),'processes':(8,1024),'tmpfs_bytes':(1024**2,4*1024**3)}
        for key,(a,b) in limits.items():
            v=getattr(self,key)
            if type(v) is not int or not a<=v<=b:raise CompilerQAError('WORKER_POLICY_INVALID: '+key)


def real_dir(path):
    p=Path(path).absolute()
    if p.is_symlink() or not p.is_dir() or any(x.is_symlink() for x in p.parents):raise CompilerQAError('WORKER_PATH_INVALID: '+str(p))
    return p


@contextmanager
def worker_slot(root, policy: WorkerPolicy, *, wait_s=0):
    root=Path(root).absolute()
    if not root.exists():root.mkdir(mode=0o700,parents=True)
    real_dir(root)
    if root.stat().st_uid!=os.getuid() or root.stat().st_mode&0o022:raise CompilerQAError('WORKER_LOCK_ROOT_UNTRUSTED')
    control=root/'policy.json';config=canonical_json({'concurrent_jobs':policy.concurrent_jobs})
    fd=os.open(control,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX)
        old=os.read(fd,1000)
        if old and old!=config:raise CompilerQAError('WORKER_CONCURRENCY_POLICY_MISMATCH')
        if not old:os.write(fd,config);os.fsync(fd)
    finally:os.close(fd)
    deadline=time.monotonic()+wait_s; held=None
    try:
        while held is None:
            for i in range(policy.concurrent_jobs):
                f=os.open(root/f'slot-{i}',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
                try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:os.close(f);continue
                held=f;break
            if held is not None:break
            if time.monotonic()>=deadline:raise CompilerQAError('WORKER_CONCURRENCY_LIMIT')
            time.sleep(.025)
        yield
    finally:
        if held is not None:os.close(held)


def run_isolated(command, *, workspace, engine=None, writable=(), policy=None, timeout_s=120,
                 cancel_event=None,max_output_bytes=2*1024**2,secrets=(),lock_root=None):
    """Return bounded-process receipt plus kernel-policy evidence. No fallback.

    Command paths in the workspace are relocated to /work. The workspace is
    read-only, except the exact directories in `writable`. The trusted engine,
    when provided, is read-only at /engine. There is no host home, host /proc,
    external network, implicit install, shell interpolation, or API-double mode.
    """
    if sys.platform!='linux' or not shutil.which('unshare'):raise CompilerQAError('WORKER_LINUX_NAMESPACES_UNAVAILABLE')
    p=policy or WorkerPolicy(); root=real_dir(workspace)
    writable=list(writable); mounts=[]
    for rel in writable:
        q=Path(rel)
        if q.is_absolute() or '..' in q.parts or not q.parts:raise CompilerQAError('WORKER_WRITE_PATH_INVALID')
        target=real_dir(root/q)
        mounts.append({'source':str(target),'target':'/work/'+q.as_posix(),'writable':True})
    # Never expose user HOME; only explicit executable/runtime directories.
    system=[]
    for loc in ('/usr','/lib','/lib64','/bin','/sbin','/opt/nvm','/opt/pyvenv','/usr/local','/etc/fonts','/etc/alternatives','/usr/share/fonts','/var/cache/fontconfig','/etc/ld.so.cache'):
        path=Path(loc)
        if path.exists() and not any(path==Path(x['source']) or path.is_relative_to(Path(x['source'])) for x in system):
            system.append({'source':str(path.resolve()),'target':loc,'writable':False})
    mounts=system+[{'source':str(root),'target':'/work','writable':False}]+mounts
    if engine is not None:mounts.append({'source':str(real_dir(engine)),'target':'/engine','writable':False})
    cmd=[]
    for arg in command:
        value=str(arg)
        if '\x00' in value:raise CompilerQAError('WORKER_COMMAND_INVALID')
        value=value.replace(str(root)+'/','/work/')
        if value==str(root):value='/work'
        if engine:value=value.replace(str(real_dir(engine))+'/','/engine/')
        cmd.append(value)
    if not cmd or not Path(cmd[0]).is_absolute():raise CompilerQAError('WORKER_ABSOLUTE_EXECUTABLE_REQUIRED')
    launcher=Path(__file__).with_name('namespace_launcher.py')
    lock_root=Path(lock_root or '/tmp/bie-comp-worker-slots')
    with worker_slot(lock_root,p,wait_s=min(5,timeout_s)),tempfile.TemporaryDirectory(prefix='bie-worker-control-') as td:
        td=Path(td); sandbox=td/'root';sandbox.mkdir(); config=td/'config.json'; proof=td/'policy.json'
        data={'command':cmd,'mounts':mounts,'root':str(sandbox),'proof':str(proof),'policy':asdict(p),
              'host_namespace_ids':{k:os.readlink('/proc/self/ns/'+k) for k in ('net','mnt','pid','user')},
              'launcher_sha256':file_identity(launcher)}
        config.write_bytes(canonical_json(data));config.chmod(0o600)
        args=[shutil.which('unshare'),'--user','--map-root-user','--mount','--net','--pid','--fork',
              '--kill-child=SIGKILL',sys.executable,'-I',str(launcher),str(config)]
        process=run_bounded_process(args,cwd=td,timeout_s=timeout_s,cancel_event=cancel_event,max_output_bytes=max_output_bytes,secrets=secrets)
        evidence=json.loads(proof.read_text()) if proof.exists() and proof.stat().st_size else {'kernel_enforced':False,'status':'NAMESPACE_SETUP_FAILED','accepted':False}
        if process.process.passed and evidence.get('kernel_enforced') is not True:
            raise CompilerQAError('WORKER_POLICY_NOT_ENFORCED')
        evidence['process_outcome']=process.outcome
        return process,evidence
