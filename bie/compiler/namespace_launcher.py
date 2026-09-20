#!/usr/bin/env python3
"""Internal H7 trusted launcher; executed with -I in new Linux namespaces."""
from pathlib import Path
import ctypes as C, errno, fcntl, json, os, resource, socket, struct, sys
lib=C.CDLL(None,use_errno=True)
lib.mount.argtypes=[C.c_char_p,C.c_char_p,C.c_char_p,C.c_ulong,C.c_char_p];lib.mount.restype=C.c_int

def mount(source,target,kind=None,flags=0,data=None):
    conv=lambda x:None if x is None else str(x).encode()
    if lib.mount(conv(source),conv(target),conv(kind),flags,conv(data))!=0:
        raise OSError(C.get_errno(),'mount '+str(target))

def main():
    config=json.loads(Path(sys.argv[1]).read_text());root=Path(config['root']);policy=config['policy']
    namespaces={k:os.readlink('/proc/self/ns/'+k) for k in ('net','mnt','pid','user')}
    if any(namespaces[k]==config['host_namespace_ids'][k] for k in namespaces):raise RuntimeError('NAMESPACE_NOT_PRIVATE')
    mount(None,'/',None,1<<14|1<<18) # recursive private propagation
    mount('tmpfs',root,'tmpfs',2|4,'size='+str(policy['tmpfs_bytes'])+',mode=755')
    for m in config['mounts']:
        dest=root/m['target'].lstrip('/');src=Path(m['source'])
        dest.parent.mkdir(parents=True,exist_ok=True)
        if src.is_dir():dest.mkdir(exist_ok=True)
        else:dest.touch()
        mount(src,dest,None,4096)
        if not m['writable']:mount(None,dest,None,4096|32|1|2|4)
    for name in ('tmp','dev','dev/shm','proc','home/worker'):(root/name).mkdir(parents=True,exist_ok=True)
    mount('tmpfs',root/'tmp','tmpfs',2|4,'size='+str(policy['tmpfs_bytes'])+',mode=1777')
    mount('tmpfs',root/'dev/shm','tmpfs',2|4,'size='+str(policy['tmpfs_bytes'])+',mode=1777')
    for name in ('null','zero','random','urandom'):
        dest=root/'dev'/name;dest.touch();mount('/dev/'+name,dest,None,4096)
    if policy['procfs']:mount('proc',root/'proc','proc',2|4|8)
    # Enable private loopback only. No interface or route to the host/external net.
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
        ifr=struct.pack('16sh',b'lo',0)
        flags=struct.unpack('16sh',fcntl.ioctl(s,0x8913,ifr))[1]
        fcntl.ioctl(s,0x8914,struct.pack('16sh',b'lo',flags|1))
    os.chdir(root);os.chroot('.');os.chdir('/work')
    resource.setrlimit(resource.RLIMIT_CPU,(policy['cpu_seconds'],policy['cpu_seconds']))
    resource.setrlimit(resource.RLIMIT_AS,(policy['address_space_bytes'],policy['address_space_bytes']))
    resource.setrlimit(resource.RLIMIT_FSIZE,(policy['file_bytes'],policy['file_bytes']))
    resource.setrlimit(resource.RLIMIT_NOFILE,(policy['descriptors'],policy['descriptors']))
    resource.setrlimit(resource.RLIMIT_NPROC,(policy['processes'],policy['processes']))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    # Resource bounds are per process/uid, not a cgroup RSS/aggregate CPU promise.
    if lib.prctl(38,1,0,0,0)!=0:raise OSError(C.get_errno(),'no_new_privs')
    for cap in range(41):lib.prctl(24,cap,0,0,0) # bounding set drop while CAP_SETPCAP is present
    class Header(C.Structure):_fields_=[('version',C.c_uint32),('pid',C.c_int)]
    class Data(C.Structure):_fields_=[('effective',C.c_uint32),('permitted',C.c_uint32),('inheritable',C.c_uint32)]
    header=Header(0x20080522,0);caps=(Data*2)()
    if lib.capset(C.byref(header),C.byref(caps))!=0:raise OSError(C.get_errno(),'drop capabilities')
    sec=C.CDLL('libseccomp.so.2',use_errno=True)
    sec.seccomp_init.argtypes=[C.c_uint32];sec.seccomp_init.restype=C.c_void_p
    sec.seccomp_syscall_resolve_name.argtypes=[C.c_char_p];sec.seccomp_syscall_resolve_name.restype=C.c_int
    sec.seccomp_rule_add.argtypes=[C.c_void_p,C.c_uint32,C.c_int,C.c_uint]
    sec.seccomp_load.argtypes=[C.c_void_p];sec.seccomp_release.argtypes=[C.c_void_p]
    ctx=sec.seccomp_init(0x7fff0000)
    denied=['mount','umount2','pivot_root','chroot','unshare','setns','ptrace','process_vm_readv','process_vm_writev',
            'bpf','keyctl','add_key','request_key','perf_event_open','open_by_handle_at','reboot','kexec_load',
            'init_module','finit_module','delete_module','swapon','swapoff','iopl','ioperm']
    for name in denied:
        nr=sec.seccomp_syscall_resolve_name(name.encode())
        if nr>=0 and sec.seccomp_rule_add(ctx,0x00050000|errno.EPERM,nr,0)!=0:raise RuntimeError('SECCOMP_RULE '+name)
    nr=sec.seccomp_syscall_resolve_name(b'clone3')
    if nr>=0:sec.seccomp_rule_add(ctx,0x00050000|errno.ENOSYS,nr,0)
    class Compare(C.Structure):_fields_=[('arg',C.c_uint),('op',C.c_int),('a',C.c_uint64),('b',C.c_uint64)]
    sec.seccomp_rule_add_array.argtypes=[C.c_void_p,C.c_uint32,C.c_int,C.c_uint,C.POINTER(Compare)]
    clone_nr=sec.seccomp_syscall_resolve_name(b'clone')
    for flag in (0x00020000,0x02000000,0x04000000,0x08000000,0x10000000,0x20000000,0x40000000):
        cmp=Compare(0,7,flag,flag)
        if sec.seccomp_rule_add_array(ctx,0x00050000|errno.EPERM,clone_nr,1,C.byref(cmp))!=0:raise RuntimeError('SECCOMP_CLONE_NAMESPACE')
    if sec.seccomp_load(ctx)!=0:raise RuntimeError('SECCOMP_LOAD')
    sec.seccomp_release(ctx)
    # Proof FD is opened by the parent-side path before chroot in a future call;
    # send through dedicated inherited descriptor, unavailable after exec.
    proof={'schema_version':'bie.linux-worker-proof.v1','kernel_enforced':True,'namespaces':namespaces,
           'private_procfs':policy['procfs'],'private_network':'LOOPBACK_ONLY_NO_HOST_ROUTE','read_only_workspace_except_declared':True,
           'capabilities_dropped':True,'no_new_privileges':True,'seccomp_denied_syscalls':denied,
           'resource_limits':policy,'launcher_sha256':config['launcher_sha256'],'accepted':False}
    os.write(PROOF_FD,json.dumps(proof,sort_keys=True).encode());os.close(PROOF_FD)
    env={'PATH':'/opt/nvm/versions/node/v22.16.0/bin:/usr/local/bin:/usr/bin:/bin',
         'HOME':'/home/worker','TMPDIR':'/tmp','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','CI':'true','NO_COLOR':'1',
         'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','PYTHONHASHSEED':'0','SOURCE_DATE_EPOCH':'0','TZ':'UTC','MPLBACKEND':'Agg','PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':'/engine/app:/engine','MPLCONFIGDIR':'/tmp/mpl','XDG_CACHE_HOME':'/tmp/cache','XDG_CONFIG_HOME':'/tmp/config'}
    os.execve(config['command'][0],config['command'],env)

if __name__=='__main__':
    cfg=json.loads(Path(sys.argv[1]).read_text())
    PROOF_FD=os.open(cfg['proof'],os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_CLOEXEC,0o600)
    try:main()
    except BaseException as exc:
        print('WORKER_SETUP_FAILED: '+str(exc),file=sys.stderr);sys.exit(125)
