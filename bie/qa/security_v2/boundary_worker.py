#!/usr/bin/env python3
"""Fixed, benign Linux x86_64 boundary diagnostics. NEVER executes supplied code.

Creates no network connection, reads no real secret, uses no kernel exploit.
Confinement is installed only on this disposable child, never on the parent.
"""
import ctypes, errno, json, os, platform, resource, signal, socket, sys, time

PROBES=('allowed_read','allowed_write','outside_read','outside_write','parent_traversal','symlink_read','inherited_fd','environment','ipv4_socket','ipv6_socket','unix_socket','spawn','exec','privilege','namespace','ptrace','file_limit','descriptor_limit')
# Native x86_64 ABI only. x32/other syscall numbers are denied by default.
ALLOW=(0,1,3,5,8,9,10,11,12,13,14,15,17,21,24,25,28,35,39,60,63,72,79,89,97,
       102,104,107,108,110,125,131,186,202,217,228,230,231,257,262,267,318,332)
class Filter(ctypes.Structure):
    _fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('k',ctypes.c_uint)]
class Program(ctypes.Structure):
    _fields_=[('len',ctypes.c_ushort),('filter',ctypes.POINTER(Filter))]
class CapHeader(ctypes.Structure):_fields_=[('version',ctypes.c_uint32),('pid',ctypes.c_int)]
class CapData(ctypes.Structure):_fields_=[('effective',ctypes.c_uint32),('permitted',ctypes.c_uint32),('inheritable',ctypes.c_uint32)]

def install_filter(lib):
    # arch != AUDIT_ARCH_X86_64 -> KILL; selected syscalls -> ALLOW; rest -> EPERM.
    rows=[(0x20,0,0,4),(0x15,1,0,0xC000003E),(0x06,0,0,0x80000000),(0x20,0,0,0)]
    for nr in ALLOW:rows.extend([(0x15,0,1,nr),(0x06,0,0,0x7fff0000)])
    # prctl permits GET queries only, never privilege/control changes.
    rows.extend([(0x15,0,5,157),(0x20,0,0,16),(0x15,2,0,39),(0x15,1,0,21),(0x06,0,0,0x00050001),(0x06,0,0,0x7fff0000),(0x06,0,0,0x00050001)])
    a=(Filter*len(rows))(*(Filter(*r) for r in rows));p=Program(len(rows),a)
    if lib.prctl(22,2,ctypes.byref(p),0,0)!=0:raise OSError(ctypes.get_errno(),'seccomp installation failed')

def run(root,case,nonce):
    base=dict(schema_version='bie.qa.boundary-child/1',case=case,nonce=nonce,
              code_executed=False,profile='LINUX_CHROOT_SECCOMP_FIXED_PROBES_V1',controls={},observations=[],status='NOT_RUN')
    if platform.system()!='Linux' or platform.machine()!='x86_64' or os.geteuid()!=0:
        base['error']='REQUIRED_BOOTSTRAP_UNAVAILABLE';return base
    lib=ctypes.CDLL(None,use_errno=True)
    try:
        if case not in ('standard','file_limit','descriptor_limit'):raise ValueError('fixed case required')
        if not os.path.isabs(root) or os.path.islink(root):raise ValueError('private root required')
        before_root=os.stat(root)
        signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        resource.setrlimit(resource.RLIMIT_CPU,(2,2))
        resource.setrlimit(resource.RLIMIT_AS,(128*1024*1024,128*1024*1024))
        resource.setrlimit(resource.RLIMIT_FSIZE,(65536,65536))
        resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
        limits=dict(cpu_limit=resource.getrlimit(resource.RLIMIT_CPU)==(2,2),memory_limit=resource.getrlimit(resource.RLIMIT_AS)==(134217728,134217728),file_limit=resource.getrlimit(resource.RLIMIT_FSIZE)==(65536,65536),descriptor_limit=resource.getrlimit(resource.RLIMIT_NOFILE)==(64,64))
        os.closerange(3,65536)
        os.environ.clear()
        os.chroot(root);os.chdir('/')
        os.setgroups([]);os.setgid(65534);os.setuid(65534)
        if lib.prctl(38,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'no_new_privs installation failed')
        h=CapHeader(0x20080522,0);caps=(CapData*2)()
        if lib.capget(ctypes.byref(h),ctypes.byref(caps))!=0:raise OSError(ctypes.get_errno(),'capability measurement failed')
        cap_zero=all(not (x.effective or x.permitted or x.inheritable) for x in caps)
        install_filter(lib)
        current=os.stat('/')
        base['controls']={**limits,'private_root':(before_root.st_dev,before_root.st_ino)==(current.st_dev,current.st_ino),
            'non_root':os.geteuid()==65534 and os.getegid()==65534,'no_capabilities':cap_zero,
            'no_new_privs':lib.prctl(39,0,0,0,0)==1,'seccomp_filter':lib.prctl(21,0,0,0,0)==2,
            'clean_environment':not os.environ,'closed_descriptors':True}
        for fd in range(3,64):
            try:os.fstat(fd);base['controls']['closed_descriptors']=False
            except OSError as e:
                if e.errno!=errno.EBADF:base['controls']['closed_descriptors']=False
        if not all(base['controls'].values()):raise RuntimeError('control measurement failed')
        obs=[]
        def record(name,allowed,call,denied=(errno.EPERM,errno.EACCES)):
            try:
                value=call()
                # Positive controls must show the expected effect, not just no exception.
                passed=bool(value) if allowed else False
                obs.append(dict(probe=name,expected='ALLOW' if allowed else 'DENY',observed='ALLOWED',errno=0,passed=passed))
            except OSError as e:obs.append(dict(probe=name,expected='ALLOW' if allowed else 'DENY',observed='DENIED',errno=e.errno,passed=not allowed and e.errno in denied))
        def read(path):
            with open(path,'rb') as f:return f.read()==b'BIE-DIAGNOSTIC-INPUT\n'
        def write(path):
            with open(path,'wb') as f:return f.write(b'BIE-DIAGNOSTIC-OUTPUT\n')==22
        def sock(family):
            s=socket.socket(family,socket.SOCK_STREAM);s.close();return True
        def raw(n,*args):
            ctypes.set_errno(0);v=lib.syscall(n,*args)
            if v<0:raise OSError(ctypes.get_errno(),'fixed diagnostic syscall denied')
            return True
        if case=='standard':
            record('allowed_read',True,lambda:read('/inputs/input.txt'))
            record('allowed_write',True,lambda:write('/outputs/result.txt'))
            record('outside_read',False,lambda:read('/outside-canary.txt'),(errno.ENOENT,errno.EACCES,errno.EPERM))
            record('outside_write',False,lambda:write('/outside-canary.txt'))
            record('parent_traversal',False,lambda:read('/../../outside-canary.txt'),(errno.ENOENT,errno.EACCES,errno.EPERM))
            record('symlink_read',False,lambda:read('/inputs/outside-link'),(errno.ENOENT,errno.EACCES,errno.EPERM))
            record('inherited_fd',False,lambda:os.read(42,1),(errno.EBADF,))
            # No actual account secret is ever provisioned.
            obs.append(dict(probe='environment',expected='ABSENT',observed='ABSENT' if not os.environ else 'PRESENT',errno=0,passed=not os.environ))
            for name,family in [('ipv4_socket',socket.AF_INET),('ipv6_socket',socket.AF_INET6),('unix_socket',socket.AF_UNIX)]:record(name,False,lambda family=family:sock(family))
            def fork():
                pid=os.fork()
                if pid==0:os._exit(0)
                return True
            record('spawn',False,fork)
            record('exec',False,lambda:os.execve('/nonexistent-program',['probe'],{}),(errno.EPERM,))
            record('privilege',False,lambda:os.setuid(0))
            record('namespace',False,lambda:raw(272,0))
            record('ptrace',False,lambda:raw(101,0,0,0,0))
        elif case=='file_limit':
            def too_large():
                f=os.open('/outputs/large.bin',os.O_CREAT|os.O_WRONLY,0o600)
                try:
                    os.write(f,b'x'*65536);os.write(f,b'x');return True
                finally:os.close(f)
            record('file_limit',False,too_large,(errno.EFBIG,))
        else:
            fds=[]
            def too_many():
                try:
                    for _ in range(70):fds.append(os.open('/inputs/input.txt',os.O_RDONLY))
                    return True
                finally:
                    for fd in fds:os.close(fd)
            record('descriptor_limit',False,too_many,(errno.EMFILE,))
        base['observations']=obs;base['status']='CHECKS_PASSED' if all(x['passed'] for x in obs) else 'BLOCKED'
    except BaseException as e:
        base['status']='NOT_RUN';base['error']=type(e).__name__+':'+str(e)[:160]
    return base
if __name__=='__main__':
    result=run(sys.argv[1],sys.argv[2],sys.argv[3]);print(json.dumps(result,sort_keys=True));sys.exit(0 if result['status']=='CHECKS_PASSED' else 4)
