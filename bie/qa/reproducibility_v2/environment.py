"""Recreate a fresh no-pip venv and measure the actual selected runtime profile.

No downloads, package installation or environment-policy bypass. The selected
stdlib hashes are not a full OS/shared-library/GPU dependency closure. Trusted
operator-registered producers only; resource limits are not a security sandbox.
"""
from __future__ import annotations
from pathlib import Path
import hashlib, os, signal, subprocess, sys, tempfile, time
from ..release_v2.contracts import ContractError, canonical_bytes, integer
from ..source_v2.codec import loads
from .models import controlled_environment, profile_object

PROBE = r'''
import hashlib, importlib, importlib.metadata, json, os, pathlib, platform, site, struct, sys
names=('json','random','pathlib','hashlib','runpy')
files={}
for n in names:
 m=importlib.import_module(n)
 p=pathlib.Path(m.__file__)
 files[n]=hashlib.sha256(p.read_bytes()).hexdigest()
cfg=pathlib.Path(sys.prefix,'pyvenv.cfg').read_text()
rows=dict((a.strip().lower(),b.strip().lower()) for line in cfg.splitlines() if '=' in line for a,b in [line.split('=',1)])
keys=('LANG','LC_ALL','TZ','PYTHONHASHSEED','PYTHONNOUSERSITE','PYTHONDONTWRITEBYTECODE','SOURCE_DATE_EPOCH','BIE_REPRO_SEED')
allowed=set(keys)|{'HOME','TMPDIR'}
if set(os.environ)-allowed:raise RuntimeError('unexpected inherited environment variable')
v=dict(profile='python-stdlib-venv-v1',python_version=platform.python_version(),implementation=platform.python_implementation(),
 python_executable_sha256=hashlib.sha256(pathlib.Path(sys.executable).read_bytes()).hexdigest(),system=platform.system(),release=platform.release(),machine=platform.machine(),
 byteorder=sys.byteorder,pointer_bits=8*struct.calcsize('P'),isolated_prefix=sys.prefix!=sys.base_prefix,
 user_site_enabled=site.ENABLE_USER_SITE,system_site_enabled=rows.get('include-system-site-packages')!='false',
 distributions=sorted(d.metadata.get('Name','unknown')+'=='+d.version for d in importlib.metadata.distributions()),
 stdlib_files=files,controlled_environment={k:os.environ.get(k) for k in keys},hash_randomization=sys.flags.hash_randomization,
 producer_protocol='request-json-output-dir-v1')
print(json.dumps(v,sort_keys=True,separators=(',',':')))
'''


def file_digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def _limits(seconds):
    import resource
    resource.setrlimit(resource.RLIMIT_CPU,(seconds,seconds+1))
    resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024*1024,16*1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))


def run_process(command,cwd,env,timeout,log_dir):
    """Fixed argv supplied by collector, never a shell command from candidate JSON."""
    if os.name!='posix':raise ContractError('REPRO_POSIX_REQUIRED')
    integer(timeout,'timeout',1,60)
    log_dir=Path(log_dir);log_dir.mkdir(parents=True,exist_ok=False)
    start=time.time_ns();clock=time.monotonic_ns();code=None;error='';p=None
    with (log_dir/'stdout.log').open('xb') as out,(log_dir/'stderr.log').open('xb') as err:
        try:
            p=subprocess.Popen(command,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                start_new_session=True,preexec_fn=lambda:_limits(timeout))
            try:code=p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:error='REPRO_WORKER_TIMEOUT'
        except OSError:error='REPRO_PROCESS_START'
        finally:
            if p is not None:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                if p.poll() is None:p.kill()
                p.wait(timeout=3)
    logs={n:(log_dir/(n+'.log')).read_bytes() for n in ('stdout','stderr')}
    if any(len(v)>1048576 for v in logs.values()):error='REPRO_LOG_LIMIT'
    return dict(started=p is not None,process_exit=code,error=error,wall_started_ns=start,
        wall_finished_ns=time.time_ns(),elapsed_ms=(time.monotonic_ns()-clock)//1000000),logs


def new_environment(parent,python,seed,epoch):
    root=Path(parent);root.mkdir(parents=True,exist_ok=False)
    home=root/'home';tmp=root/'tmp';home.mkdir();tmp.mkdir()
    env={**controlled_environment(seed,epoch),'HOME':str(home),'TMPDIR':str(tmp)}
    interpreter=Path(python).resolve()
    if not interpreter.is_file() or not interpreter.is_absolute():raise ContractError('REPRO_PYTHON_EXECUTABLE')
    process,logs=run_process([str(interpreter),'-I','-B','-m','venv','--copies','--without-pip',str(root/'venv')],root,env,30,root/'bootstrap')
    if process['error'] or process['process_exit']!=0:raise ContractError('REPRO_ENVIRONMENT_BUILD')
    executable=root/'venv/bin/python'
    if executable.is_symlink() or not executable.is_file():raise ContractError('REPRO_INTERPRETER_NOT_COPIED')
    return executable,env,process,logs


def measure(executable,env,destination):
    process,logs=run_process([str(executable),'-s','-B','-P','-c',PROBE],Path(executable).parent,env,10,destination)
    if process['error'] or process['process_exit']!=0:raise ContractError('REPRO_ENVIRONMENT_PROBE')
    value=loads(logs['stdout']);raw=canonical_bytes(value).decode();profile_object(raw)
    return value,process


def capture_environment(*,python=getattr(sys,"_base_executable",sys.executable),seed=17,source_date_epoch=0):
    """Actual bounded recipe capture; generated profile still requires operator approval."""
    integer(seed,'seed',0,2**32-1);integer(source_date_epoch,'epoch')
    with tempfile.TemporaryDirectory(prefix='bie-repro-recipe-') as temp:
        exe,env,_,_=new_environment(Path(temp)/'capture',python,seed,source_date_epoch)
        measured,_=measure(exe,env,Path(temp)/'probe')
        return canonical_bytes(measured).decode()
