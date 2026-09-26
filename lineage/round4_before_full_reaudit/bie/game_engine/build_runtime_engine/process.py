from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import ctypes, os, resource, subprocess, shutil
from .errors import GameBuildError
@dataclass(frozen=True)
class ProcessResult:
    returncode:int;stdout:str;stderr:str

_SAFE_BASE_PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
def sanitized_environment(command0,extra=None):
    parents=[str(Path(command0).absolute().parent)]
    node=shutil.which('node')
    if node:parents.append(str(Path(node).absolute().parent))
    path=':'.join(dict.fromkeys(parents))+':'+_SAFE_BASE_PATH
    env={'PATH':path,'HOME':'/tmp','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC','PYTHONHASHSEED':'0','NO_COLOR':'1'}
    if extra:
        allowed={'TMPDIR','TEMP','TMP','BIE_PROCESS_TAG'}
        unknown=set(extra)-allowed
        if unknown:raise GameBuildError('GAME_BUILD_PROCESS_ENV_KEY_FORBIDDEN',','.join(sorted(unknown)))
        env.update({k:str(v) for k,v in extra.items()})
    return env

def _limits(cpu_seconds,memory_bytes,max_processes,max_open_files,max_file_bytes):
    def apply():
        os.umask(0o077)
        resource.setrlimit(resource.RLIMIT_CPU,(cpu_seconds,cpu_seconds+1))
        if memory_bytes>0:resource.setrlimit(resource.RLIMIT_AS,(memory_bytes,memory_bytes))
        resource.setrlimit(resource.RLIMIT_NPROC,(max_processes,max_processes))
        resource.setrlimit(resource.RLIMIT_NOFILE,(max_open_files,max_open_files))
        resource.setrlimit(resource.RLIMIT_FSIZE,(max_file_bytes,max_file_bytes))
        try:
            libc=ctypes.CDLL(None);PR_SET_NO_NEW_PRIVS=38
            if libc.prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)!=0:os._exit(126)
        except Exception:os._exit(126)
    return apply

def run_bounded(cmd,*,cwd=None,timeout=30,max_output=1_000_000,env=None,cpu_seconds=45,memory_bytes=1_500_000_000,max_processes=128,max_open_files=256,max_file_bytes=100_000_000):
    cmd=list(cmd)
    if not cmd:raise GameBuildError('GAME_BUILD_PROCESS_COMMAND_REQUIRED')
    clean=sanitized_environment(cmd[0],env)
    try:
        p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=timeout,env=clean,start_new_session=True,
             preexec_fn=_limits(cpu_seconds,memory_bytes,max_processes,max_open_files,max_file_bytes))
    except subprocess.TimeoutExpired as e:raise GameBuildError('GAME_BUILD_PROCESS_TIMEOUT',str(cmd[0])) from e
    except OSError as e:raise GameBuildError('GAME_BUILD_PROCESS_LAUNCH',str(cmd[0])) from e
    if len(p.stdout.encode())+len(p.stderr.encode())>max_output:raise GameBuildError('GAME_BUILD_PROCESS_OUTPUT_LIMIT')
    return ProcessResult(p.returncode,p.stdout,p.stderr)
